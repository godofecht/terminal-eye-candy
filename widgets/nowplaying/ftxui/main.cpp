#include <ftxui/component/component.hpp>
#include <ftxui/component/screen_interactive.hpp>
#include <ftxui/dom/elements.hpp>
#include <ftxui/screen/color.hpp>

#include <algorithm>
#include <atomic>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <mutex>
#include <string>
#include <thread>
#include <vector>

using namespace ftxui;
using namespace std::chrono_literals;
using Clock = std::chrono::steady_clock;

// ── utils ────────────────────────────────────────────────────────────────────

static std::string sh(const std::string& cmd) {
    std::string out;
    FILE* f = popen(cmd.c_str(), "r");
    if (!f) return {};
    char buf[512];
    while (fgets(buf, sizeof buf, f)) out += buf;
    pclose(f);
    while (!out.empty() && (out.back()=='\n' || out.back()=='\r')) out.pop_back();
    return out;
}

static std::vector<std::string> split_on(const std::string& s, const std::string& d) {
    std::vector<std::string> r;
    size_t i=0, p;
    while ((p=s.find(d,i))!=std::string::npos) { r.push_back(s.substr(i,p-i)); i=p+d.size(); }
    r.push_back(s.substr(i));
    return r;
}

static std::string fmt(int s) {
    s=std::max(0,s); char b[16]; snprintf(b,sizeof b,"%d:%02d",s/60,s%60); return b;
}

// ── track ────────────────────────────────────────────────────────────────────

struct Track { std::string app,title,artist; int pos=0,dur=1; bool playing=false,valid=false; };

static Track fetch_app(const std::string& app, const std::string& dur_expr) {
    std::string cmd =
        "osascript"
        " -e 'tell application \"System Events\"'"
        " -e '  if exists process \"" + app + "\" then'"
        " -e '    tell application \"" + app + "\"'"
        " -e '      set s to player state'"
        " -e '      if s is playing or s is paused then'"
        " -e '        set p to (player position as integer)'"
        " -e '        set d to (" + dur_expr + ")'"
        " -e '        return name of current track & \"||\" & artist of current track"
                       " & \"||\" & p & \"||\" & d & \"||\" & (s as string)'"
        " -e '      end if'"
        " -e '    end tell'"
        " -e '  end if'"
        " -e 'end tell' 2>/dev/null";
    auto raw = sh(cmd);
    if (raw.empty()) return {};
    auto p = split_on(raw,"||");
    if (p.size()<4) return {};
    Track t; t.app=app; t.title=p[0]; t.artist=p[1];
    try{t.pos=std::stoi(p[2]);}catch(...){}
    try{t.dur=std::max(1,std::stoi(p[3]));}catch(...){}
    t.playing = p.size()>4 && p[4].find("playing")!=std::string::npos;
    t.valid=true; return t;
}

static Track fetch() {
    auto t = fetch_app("Spotify","duration of current track / 1000 as integer");
    if (t.valid) return t;
    return fetch_app("Music","duration of current track as integer");
}

static void async_sh(std::string cmd) { std::thread([cmd]{sh(cmd);}).detach(); }

static void do_seek(const Track& t, int pos) {
    async_sh("osascript -e 'tell application \""+t.app+"\" to set player position to "
             +std::to_string(pos)+"' 2>/dev/null");
}
static void do_pp(const Track& t) {
    async_sh("osascript -e 'tell application \""+t.app+"\" to playpause' 2>/dev/null");
}
static void do_vol(const Track& t, int d) {
    std::string expr = d>0 ? "min(sound volume+10,100)" : "max(sound volume-10,0)";
    async_sh("osascript -e 'tell application \""+t.app+"\" to set sound volume to "+expr+"' 2>/dev/null");
}

// ── main ─────────────────────────────────────────────────────────────────────

int main() {
    auto screen = ScreenInteractive::Fullscreen();

    std::mutex        mtx;
    Track             track;
    double            local_pos = 0.0;
    std::atomic<bool> alive{true};
    std::atomic<int>  frame{0};

    // Timestamps for grace-period logic
    auto last_seek_tp = Clock::now() - 10s;  // last time WE issued a seek
    auto last_drag_tp = Clock::now() - 10s;  // last time user moved slider

    // Pending seek (debounced) ──────────────────────────────────────────────
    // Set from renderer; executed by seeker thread 200 ms after last drag.
    std::mutex seek_mtx;
    int        pending_pos = -1;

    std::thread seeker([&]{
        while (alive) {
            std::this_thread::sleep_for(30ms);
            int pos = -1;
            Track tc;
            {
                std::lock_guard lk(seek_mtx);
                if (pending_pos >= 0 && Clock::now()-last_drag_tp > 200ms) {
                    pos = pending_pos;
                    pending_pos = -1;
                }
            }
            if (pos >= 0) {
                { std::lock_guard lk(mtx); tc = track; }
                do_seek(tc, pos);
                { std::lock_guard lk(seek_mtx); last_seek_tp = Clock::now(); }
            }
        }
    });

    // Poll thread ──────────────────────────────────────────────────────────
    std::thread poller([&]{
        while (alive) {
            auto t = fetch();
            {
                std::lock_guard lk(mtx);
                bool new_trk = !track.valid || t.title != track.title;
                track = t;
                if (t.valid) {
                    bool in_grace = Clock::now()-last_seek_tp < 3s;
                    bool in_drag  = Clock::now()-last_drag_tp  < 1s;
                    // Only sync position from source when we're not in the middle of seeking
                    if (!in_grace && !in_drag) {
                        if (new_trk || std::abs((double)t.pos - local_pos) > 2.0)
                            local_pos = t.pos;
                    }
                }
            }
            screen.PostEvent(Event::Custom);
            for (int i=0; i<20 && alive; ++i) std::this_thread::sleep_for(100ms);
        }
    });

    // Tick thread ──────────────────────────────────────────────────────────
    std::thread ticker([&]{
        while (alive) {
            std::this_thread::sleep_for(100ms);
            {
                std::lock_guard lk(mtx);
                bool in_drag = Clock::now()-last_drag_tp < 100ms;
                if (track.valid && track.playing && !in_drag)
                    local_pos = std::min(local_pos+0.1, (double)track.dur);
            }
            ++frame;
            screen.PostEvent(Event::Custom);
        }
    });

    // Slider (0..10000) ────────────────────────────────────────────────────
    // sv_ours: the value WE set.  If sv != sv_ours → FTXUI changed it → user dragged.
    int sv      = 0;
    int sv_ours = 0;   // last value we wrote to sv

    auto slider = Slider("", &sv, 0, 10000, 1);

    auto root = CatchEvent(slider, [&](Event e) {
        std::lock_guard lk(mtx);
        if (!track.valid) return false;
        if (e == Event::ArrowLeft)  {
            local_pos = std::max(local_pos-5.0, 0.0);
            { std::lock_guard lk2(seek_mtx); pending_pos=(int)local_pos; last_drag_tp=Clock::now(); }
            return true;
        }
        if (e == Event::ArrowRight) {
            local_pos = std::min(local_pos+5.0, (double)track.dur);
            { std::lock_guard lk2(seek_mtx); pending_pos=(int)local_pos; last_drag_tp=Clock::now(); }
            return true;
        }
        if (e == Event::ArrowUp)   { do_vol(track,+1); return true; }
        if (e == Event::ArrowDown) { do_vol(track,-1); return true; }
        if (e == Event::Character(' ')) {
            do_pp(track); track.playing=!track.playing; return true;
        }
        if (e == Event::Character('q') || e == Event::Escape) {
            screen.ExitLoopClosure()(); return true;
        }
        return false;
    });

    auto renderer = Renderer(root, [&]() -> Element {
        std::lock_guard lk(mtx);

        // ── drag detection ──────────────────────────────────────────────────
        // FTXUI changed sv (user dragged mouse) if sv != what we last wrote.
        if (sv != sv_ours) {
            last_drag_tp = Clock::now();
            local_pos    = track.valid ? sv * track.dur / 10000.0 : 0.0;
            {
                std::lock_guard lk2(seek_mtx);
                pending_pos = (int)local_pos;
            }
        }

        // Drive slider from local_pos only when user isn't touching it
        bool in_drag = Clock::now()-last_drag_tp < 150ms;
        if (!in_drag && track.valid && track.dur > 0) {
            sv = (int)(local_pos / track.dur * 10000.0);
        }
        sv_ours = sv;

        // ── empty state ─────────────────────────────────────────────────────
        if (!track.valid) {
            return vbox({
                filler(),
                text("  ♪   nothing playing") | dim | hcenter,
                text("  open Spotify or Apple Music") | dim | hcenter,
                filler(),
                separator(),
                text("q quit") | dim | hcenter,
            }) | border;
        }

        // ── equalizer ───────────────────────────────────────────────────────
        const char* bch = " ._-=+|*#";
        Elements eq_els;
        for (int i=0; i<16; ++i) {
            int h = track.playing
                ? (int)(std::abs(std::sin(frame*0.28+i*0.75))*7)
                : 0;
            auto col = track.playing ? Color::Green : Color::GrayDark;
            eq_els.push_back(text(std::string(1,bch[std::clamp(h,0,8)])) | color(col));
        }

        // ── layout ──────────────────────────────────────────────────────────
        auto title_row = hbox({
            hbox(eq_els),
            text("  "),
            text(track.title) | bold,
            text("  "),
            text("["+track.app+"]") | dim,
        });

        auto artist_row = hbox({
            text(std::string(18,' ')),
            text(track.artist) | color(Color::Yellow),
        });

        auto time_row = hbox({
            text(" "+fmt((int)local_pos)+" ") | dim,
            root->Render() | flex,
            text(" "+fmt(track.dur)+" ") | dim,
        });

        std::string state_str = track.playing ? "> playing" : "| paused";
        auto state_col = track.playing ? Color::Green : Color::GrayDark;

        auto status_row = hbox({
            text("  "+state_str) | color(state_col),
            filler(),
            text("<- -> seek   ^ v vol   spc pause   q quit  ") | dim,
        });

        return vbox({
            title_row,
            artist_row,
            separator(),
            time_row,
            separator(),
            status_row,
        }) | border;
    });

    screen.Loop(renderer);
    alive = false;
    poller.join();
    seeker.join();
    ticker.join();
    return 0;
}
