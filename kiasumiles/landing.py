from __future__ import annotations


def render_landing(version: dict) -> str:
    data_version = version["data_version"]
    cards = version["cards"]
    merchants = version["merchants"]

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="KiasuMiles is a hosted MCP service for Singapore credit-card miles recommendations, without storing user wallet data.">
  <title>KiasuMiles | Your cards. Your merchants. Your best answer.</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #fbfbfd;
      --ink: #1d1d1f;
      --muted: #5f626b;
      --soft: #f5f5f7;
      --line: rgba(0, 0, 0, 0.10);
      --blue: #0071e3;
      --blue-dark: #005bb8;
      --green: #19a35b;
      --shadow: 0 28px 90px rgba(0, 0, 0, 0.08);
      --shadow-strong: 0 44px 140px rgba(0, 0, 0, 0.11);
    }}

    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", sans-serif;
      -webkit-font-smoothing: antialiased;
      text-rendering: optimizeLegibility;
    }}
    img, video {{ display: block; max-width: 100%; }}
    a {{ color: inherit; text-decoration: none; }}
    p, h1, h2, h3 {{ margin: 0; }}
    code {{
      font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
      font-size: 0.92em;
    }}

    .top-haze {{
      pointer-events: none;
      position: fixed;
      inset: 0 0 auto;
      z-index: 20;
      height: 96px;
      background: linear-gradient(180deg, var(--bg), rgba(251, 251, 253, 0.82), rgba(251, 251, 253, 0));
    }}

    .nav {{
      position: sticky;
      top: 0;
      z-index: 30;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 20px;
      max-width: 1280px;
      margin: 0 auto;
      padding: 20px clamp(20px, 4vw, 32px);
      color: #3f4249;
      font-size: 14px;
      font-weight: 650;
      backdrop-filter: blur(18px);
    }}
    .brand {{ color: var(--ink); letter-spacing: -0.02em; }}
    .nav-links {{ display: flex; align-items: center; gap: 28px; }}
    .nav-actions {{ display: flex; align-items: center; gap: 10px; }}
    .nav a:hover {{ color: #050507; }}

    .button {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 10px;
      border-radius: 999px;
      padding: 12px 18px;
      font-weight: 750;
      transition: transform 180ms ease, background 180ms ease, color 180ms ease;
    }}
    .button:hover {{ transform: translateY(-1px); }}
    .button-blue {{ background: var(--blue); color: #fff; }}
    .button-blue:hover {{ background: #0068d1; color: #fff; }}
    .button-dark {{ background: #050507; color: #fff; }}
    .button-light {{ background: #fff; color: #050507; }}
    .button-outline {{ border: 1px solid rgba(255,255,255,0.24); color: #fff; }}
    .button-outline:hover {{ background: rgba(255,255,255,0.10); color: #fff; }}

    .hero-wrap {{
      max-width: 1500px;
      margin: 0 auto;
      padding: clamp(28px, 5vw, 54px) clamp(20px, 4vw, 32px) 86px;
    }}
    .hero-media {{
      overflow: hidden;
      border: 1px solid var(--line);
      border-radius: clamp(28px, 5vw, 52px);
      background: #fff;
      box-shadow: var(--shadow-strong);
    }}
    .sr-only {{
      position: absolute;
      width: 1px;
      height: 1px;
      padding: 0;
      margin: -1px;
      overflow: hidden;
      clip: rect(0, 0, 0, 0);
      white-space: nowrap;
      border: 0;
    }}

    .hero-grid {{
      display: grid;
      grid-template-columns: minmax(0, 1.05fr) minmax(320px, 0.95fr);
      align-items: center;
      gap: 20px;
      max-width: 1120px;
      margin: 40px auto 0;
    }}
    .intro-card, .install-card, .story-card, .lesson-card, .feature-card, .examples-panel {{
      border: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.88);
      box-shadow: 0 18px 58px rgba(0, 0, 0, 0.045);
    }}
    .intro-card {{
      border-radius: 28px;
      padding: clamp(22px, 3vw, 30px);
      backdrop-filter: blur(16px);
    }}
    .label {{
      color: var(--blue);
      font-size: 18px;
      font-weight: 750;
    }}
    .micro-label {{
      color: #8b8e96;
      font-size: 13px;
      font-weight: 800;
      letter-spacing: 0.10em;
      text-transform: uppercase;
    }}
    .body-lg {{
      color: var(--muted);
      font-size: clamp(18px, 2vw, 22px);
      line-height: 1.45;
      letter-spacing: -0.006em;
    }}
    .body-md {{
      color: var(--muted);
      font-size: 18px;
      line-height: 1.45;
    }}

    .install-card {{
      border-radius: 30px;
      padding: clamp(22px, 3vw, 28px);
      background: #fff;
      box-shadow: var(--shadow);
    }}
    .pill {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      border-radius: 999px;
      background: #eef5ff;
      color: var(--blue);
      padding: 9px 14px;
      font-size: 14px;
      font-weight: 800;
    }}
    .install-card h2 {{
      margin-top: 18px;
      color: #050507;
      font-size: clamp(30px, 4vw, 42px);
      line-height: 1.05;
      letter-spacing: -0.012em;
    }}
    .endpoint {{
      display: block;
      margin-top: 20px;
      border-radius: 20px;
      background: #050507;
      color: #fff;
      padding: 18px 20px;
    }}
    .endpoint span {{
      display: block;
      color: rgba(255,255,255,0.58);
      font-size: 12px;
      font-weight: 800;
      letter-spacing: 0.10em;
      text-transform: uppercase;
    }}
    .endpoint code {{
      display: block;
      margin-top: 6px;
      overflow-wrap: anywhere;
      font-size: clamp(15px, 2vw, 18px);
      font-weight: 750;
    }}
    .card-actions {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
      margin-top: 16px;
    }}

    .section {{
      max-width: 1280px;
      margin: 0 auto;
      padding: clamp(78px, 9vw, 128px) clamp(20px, 4vw, 32px);
    }}
    .section-center {{
      max-width: 850px;
      margin: 0 auto;
      text-align: center;
    }}
    h2 {{
      margin-top: 14px;
      color: #050507;
      font-size: clamp(42px, 7vw, 84px);
      line-height: 1.04;
      letter-spacing: -0.018em;
      text-wrap: balance;
    }}
    h3 {{
      color: #050507;
      font-size: clamp(25px, 3vw, 34px);
      line-height: 1.08;
      letter-spacing: -0.012em;
      text-wrap: balance;
    }}

    .story-grid {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 20px;
      margin-top: 64px;
    }}
    .story-card {{
      border-radius: 32px;
      padding: clamp(26px, 3vw, 34px);
      background: #fff;
      box-shadow: var(--shadow);
    }}
    .phase {{
      display: inline-flex;
      margin-bottom: 30px;
      border-radius: 999px;
      background: var(--soft);
      color: var(--blue);
      padding: 9px 14px;
      font-size: 14px;
      font-weight: 800;
    }}
    .muted-small {{
      margin-top: 18px;
      color: #777b84;
      font-size: 16px;
      line-height: 1.44;
    }}

    .lesson-grid {{
      display: grid;
      grid-template-columns: 0.95fr 1.05fr;
      gap: 20px;
      margin-top: 28px;
    }}
    .lesson-card {{
      border-radius: 32px;
      padding: clamp(28px, 4vw, 42px);
    }}
    .lesson-card.soft {{ background: var(--soft); box-shadow: none; }}
    .lesson-list {{
      display: grid;
      gap: 14px;
      margin-top: 22px;
    }}
    .lesson-item {{
      display: flex;
      gap: 14px;
      border-radius: 18px;
      background: var(--bg);
      padding: 16px;
      color: #474b53;
      font-size: 18px;
      line-height: 1.35;
    }}
    .check {{
      display: inline-flex;
      flex: 0 0 auto;
      width: 28px;
      height: 28px;
      align-items: center;
      justify-content: center;
      border-radius: 999px;
      background: var(--blue);
      color: #fff;
      font-weight: 900;
    }}

    .section-head {{
      display: flex;
      align-items: end;
      justify-content: space-between;
      gap: 24px;
      margin-bottom: 40px;
    }}
    .section-head p:last-child {{
      max-width: 420px;
    }}
    .video-frame {{
      overflow: hidden;
      border: 1px solid var(--line);
      border-radius: 36px;
      background: #fff;
      box-shadow: var(--shadow-strong);
    }}
    .video-frame video {{
      width: 100%;
      aspect-ratio: 16 / 9;
      background: #fff;
    }}

    .answer-section {{
      display: grid;
      grid-template-columns: 0.9fr 1.1fr;
      align-items: center;
      gap: clamp(44px, 7vw, 88px);
    }}
    .phone {{
      width: min(100%, 360px);
      aspect-ratio: 9 / 16;
      margin: 0 auto;
      border-radius: 44px;
      background: #050507;
      padding: 8px;
      box-shadow: 0 42px 120px rgba(0, 0, 0, 0.18);
    }}
    .phone-screen {{
      height: 100%;
      overflow: hidden;
      border-radius: 38px;
      background: #fff;
      padding: 30px 20px;
    }}
    .phone-status {{
      display: flex;
      justify-content: space-between;
      margin-bottom: 34px;
      color: #9a9da5;
      font-size: 12px;
      font-weight: 750;
    }}
    .bubble {{
      max-width: 250px;
      border-radius: 22px;
      padding: 16px 18px;
      font-size: 18px;
      font-weight: 750;
      line-height: 1.18;
    }}
    .bubble.ask {{ margin-left: auto; background: var(--blue); color: #fff; }}
    .bubble.answer {{ margin-top: 18px; background: var(--soft); color: #050507; }}
    .phone-card {{
      margin-top: 22px;
      border: 1px solid var(--line);
      border-radius: 26px;
      background: var(--bg);
      padding: 20px;
    }}
    .phone-card .title {{
      margin-top: 4px;
      color: #050507;
      font-size: 25px;
      font-weight: 850;
      letter-spacing: -0.012em;
    }}
    .meter {{
      height: 8px;
      overflow: hidden;
      margin-top: 18px;
      border-radius: 999px;
      background: #dedfe4;
    }}
    .meter span {{
      display: block;
      width: 78%;
      height: 100%;
      border-radius: inherit;
      background: var(--green);
    }}

    .feature-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 20px;
      margin-top: 54px;
    }}
    .feature-card {{
      border-radius: 28px;
      background: #fff;
      padding: 30px;
      transition: transform 180ms ease, box-shadow 180ms ease;
    }}
    .feature-card:hover {{
      transform: translateY(-4px);
      box-shadow: 0 28px 90px rgba(0, 0, 0, 0.075);
    }}
    .feature-icon {{
      display: flex;
      width: 44px;
      height: 44px;
      align-items: center;
      justify-content: center;
      margin-bottom: 26px;
      border-radius: 999px;
      background: var(--soft);
      color: var(--blue);
      font-weight: 900;
    }}

    .examples-panel {{
      border-radius: 42px;
      background: #fff;
      padding: clamp(24px, 4vw, 48px);
      box-shadow: var(--shadow-strong);
    }}
    .examples-grid {{
      display: grid;
      grid-template-columns: 0.8fr 1.2fr;
      align-items: center;
      gap: 42px;
    }}
    .examples-list {{ display: grid; gap: 14px; }}
    .example {{
      border-radius: 24px;
      background: var(--soft);
      padding: 22px;
    }}
    .question {{
      color: var(--muted);
      font-size: 16px;
      font-weight: 750;
    }}
    .example-row {{
      display: flex;
      align-items: end;
      justify-content: space-between;
      gap: 16px;
      margin-top: 8px;
    }}
    .example-answer {{
      color: #050507;
      font-size: clamp(24px, 3vw, 34px);
      font-weight: 850;
      letter-spacing: -0.012em;
    }}
    .example-note {{
      color: var(--muted);
      font-size: 14px;
      font-weight: 750;
      white-space: nowrap;
    }}

    .final-cta {{
      position: relative;
      overflow: hidden;
      border-radius: 48px;
      background: #050507;
      color: #fff;
      padding: clamp(48px, 8vw, 92px) clamp(28px, 6vw, 68px);
      box-shadow: 0 44px 140px rgba(0, 0, 0, 0.14);
    }}
    .glow-one, .glow-two {{
      position: absolute;
      width: 320px;
      height: 320px;
      border-radius: 999px;
      filter: blur(54px);
    }}
    .glow-one {{ right: -90px; top: -90px; background: rgba(0, 113, 227, 0.36); }}
    .glow-two {{ left: 60px; bottom: -110px; background: rgba(25, 163, 91, 0.24); }}
    .final-content {{ position: relative; z-index: 1; max-width: 860px; }}
    .final-cta h2 {{ color: #fff; }}
    .final-cta .body-lg {{ color: rgba(255,255,255,0.66); max-width: 680px; }}
    .final-actions {{
      display: flex;
      flex-wrap: wrap;
      gap: 14px;
      margin-top: 34px;
    }}
    .meta-line {{
      margin-top: 28px;
      color: rgba(255,255,255,0.55);
      font-size: 14px;
      line-height: 1.45;
    }}

    @media (max-width: 860px) {{
      .nav-links {{ display: none; }}
      .hero-grid,
      .story-grid,
      .lesson-grid,
      .answer-section,
      .examples-grid {{
        grid-template-columns: 1fr;
      }}
      .section-head {{
        align-items: start;
        flex-direction: column;
      }}
      .card-actions {{
        grid-template-columns: 1fr;
      }}
      .example-row {{
        align-items: start;
        flex-direction: column;
      }}
    }}

    @media (max-width: 560px) {{
      .nav {{ padding-top: 14px; }}
      .nav-actions .button-blue {{ display: none; }}
      .button {{ width: 100%; }}
      .nav-actions .button {{ width: auto; }}
      .hero-wrap {{ padding-bottom: 48px; }}
      .section {{ padding-top: 68px; padding-bottom: 68px; }}
      .hero-media {{ border-radius: 24px; }}
      .install-card, .intro-card, .story-card, .lesson-card, .feature-card {{ border-radius: 24px; }}
      .video-frame {{ border-radius: 24px; }}
      .examples-panel, .final-cta {{ border-radius: 28px; }}
    }}

    @media (prefers-reduced-motion: reduce) {{
      *, *::before, *::after {{
        scroll-behavior: auto !important;
        transition-duration: 0.001ms !important;
        animation-duration: 0.001ms !important;
        animation-iteration-count: 1 !important;
      }}
    }}
  </style>
</head>
<body>
  <div class="top-haze"></div>
  <nav class="nav" aria-label="Primary navigation">
    <a href="#top" class="brand">KiasuMiles</a>
    <div class="nav-links" aria-label="Page sections">
      <a href="#story">Story</a>
      <a href="#demo">Demo</a>
      <a href="#features">Features</a>
      <a href="/privacy">Privacy</a>
    </div>
    <div class="nav-actions">
      <a class="button button-blue" href="#use-hosted">Connect MCP</a>
      <a class="button button-dark" href="https://github.com/hosanxiv/kiasumiles" rel="noreferrer">GitHub</a>
    </div>
  </nav>

  <main>
    <section id="top" class="hero-wrap">
      <h1 class="sr-only">KiasuMiles. Your cards. Your merchants. Your best answer.</h1>
      <div class="hero-media">
        <img src="/kiasumiles/hero.png" width="1200" height="630" alt="KiasuMiles hero with the line Your cards. Your merchants. Your best answer beside a personalized card recommendation.">
      </div>
      <div class="hero-grid">
        <div class="intro-card">
          <p class="micro-label">Built by Hosan</p>
          <p class="body-lg" style="margin-top: 12px;">
            KiasuMiles is a hosted MCP service for the cashier moment: your agent sends the merchant and the user's current card stack, then gets the best card before the tap.
          </p>
        </div>
        <div id="use-hosted" class="install-card">
          <span class="pill">Hosted MCP endpoint</span>
          <h2>Connect your agent. Keep wallet data client-side.</h2>
          <p class="body-md" style="margin-top: 12px;">
            The hosted server stores card rules and merchant data. Your client sends card IDs per request, and KiasuMiles does not store a wallet.
          </p>
          <a class="endpoint" href="/mcp" aria-label="Hosted MCP endpoint">
            <span>Streamable HTTP MCP endpoint</span>
            <code>https://kiasumiles.space/mcp</code>
          </a>
          <div class="card-actions">
            <a class="button button-dark" href="/privacy">Read privacy policy</a>
            <a class="button button-blue" href="https://github.com/hosanxiv/kiasumiles" rel="noreferrer">View GitHub</a>
          </div>
        </div>
      </div>
    </section>

    <section id="story" class="section">
      <div class="section-center">
        <p class="label">The story</p>
        <h2>I built KiasuMiles because "roughly right" was costing real miles.</h2>
        <p class="body-lg" style="margin-top: 26px;">
          The spark was a repeated human moment: standing at checkout, knowing the right card probably exists, but not knowing it quickly enough to use it.
        </p>
      </div>
      <div class="story-grid">
        <article class="story-card">
          <span class="phase">The moment</span>
          <h3>The ritual was small enough to ignore.</h3>
          <p class="body-md" style="margin-top: 18px;">At the cashier, my wife would look at her wallet, look at me, and ask: "Which card?" I usually had an answer. "Usually" is where miles disappear quietly.</p>
          <p class="muted-small">One confident tap can turn 4 mpd into base rate. You find out days later, if you bother checking the statement at all.</p>
        </article>
        <article class="story-card">
          <span class="phase">The build</span>
          <h3>The product became an MCP server.</h3>
          <p class="body-md" style="margin-top: 18px;">The early build leaned on extra setup steps. Useful for experiments, but too much ceremony for the checkout line.</p>
          <p class="muted-small">Now the hosted endpoint keeps the rules current while clients pass the user's card IDs for each request.</p>
        </article>
        <article class="story-card">
          <span class="phase">The tap</span>
          <h3>The answer moved to the moment that matters.</h3>
          <p class="body-md" style="margin-top: 18px;">Different card sets can produce different answers for the same merchant, so the recommendation is always based on the cards passed in with that request.</p>
          <p class="muted-small">The whole product lives in the few seconds before the tap. That is the only window that matters.</p>
        </article>
      </div>
      <div class="lesson-grid">
        <div class="lesson-card soft">
          <p class="micro-label">From the build</p>
          <h3 style="margin-top: 16px;">The data can be right and the recommendation can still be wrong.</h3>
          <p class="body-md" style="margin-top: 18px;">
            Category-level advice breaks when the merchant has specific rules. KiasuMiles combines merchant matching, card-rule caveats, and the cards supplied in the request before ranking.
          </p>
        </div>
        <div class="lesson-card">
          <p class="micro-label">What changed</p>
          <div class="lesson-list">
            <div class="lesson-item"><span class="check">&check;</span><span>Card IDs are passed in with each MCP request, then ranked against the merchant.</span></div>
            <div class="lesson-item"><span class="check">&check;</span><span>Merchant logic handles exceptions instead of trusting category alone.</span></div>
            <div class="lesson-item"><span class="check">&check;</span><span>When card rules are time-sensitive, KiasuMiles shows the caveat instead of bluffing certainty.</span></div>
          </div>
        </div>
      </div>
    </section>

    <section id="demo" class="section">
      <div class="section-head">
        <div>
          <p class="label">60-second product film</p>
          <h2 style="font-size: clamp(38px, 6vw, 72px);">Ask, rank, tap, move on.</h2>
        </div>
        <p class="body-md">A quick look at the kind of question an MCP-connected agent can answer in the moment.</p>
      </div>
      <div class="video-frame">
        <video src="/kiasumiles/product-demo-60s.mp4" controls playsinline preload="metadata" poster="/kiasumiles/hero.png"></video>
      </div>
    </section>

    <section class="section answer-section">
      <div>
        <p class="label">The answer</p>
        <h2>Ask your agent. Get the card.</h2>
        <p class="body-lg" style="margin-top: 26px;">
          KiasuMiles starts with the cards supplied in the MCP request, then recommends the best usable card for the merchant in front of you.
        </p>
      </div>
      <div class="phone" aria-label="Example mobile chat with KiasuMiles recommendation">
        <div class="phone-screen">
          <div class="phone-status"><span>9:41</span><span>&bull;&bull;&bull;</span></div>
          <div class="bubble ask">What card at Sheng Siong?</div>
          <div class="bubble answer">Use UOB Preferred Platinum Visa.</div>
          <div class="phone-card">
            <div class="muted-small" style="margin-top: 0;">Top pick · 4 mpd</div>
            <div class="title">UOB Preferred Platinum Visa</div>
            <div class="meter"><span></span></div>
            <div class="muted-small">Ranked from the cards sent with this request</div>
          </div>
        </div>
      </div>
    </section>

    <section id="features" class="section">
      <div style="max-width: 780px;">
        <p class="label">Features</p>
        <h2>Built for the person at the counter.</h2>
      </div>
      <div class="feature-grid">
        <article class="feature-card">
          <div class="feature-icon">&check;</div>
          <h3>Stack-aware ranking</h3>
          <p class="body-md" style="margin-top: 12px;">Pass card IDs in the MCP request and rank only those cards against the merchant.</p>
        </article>
        <article class="feature-card">
          <div class="feature-icon">&check;</div>
          <h3>Merchant-aware logic</h3>
          <p class="body-md" style="margin-top: 12px;">Looks beyond broad categories and handles merchant-specific caveats where the rules require it.</p>
        </article>
        <article class="feature-card">
          <div class="feature-icon">&check;</div>
          <h3>No hosted wallet</h3>
          <p class="body-md" style="margin-top: 12px;">The hosted service does not expose wallet configure or wallet read tools.</p>
        </article>
        <article class="feature-card">
          <div class="feature-icon">&check;</div>
          <h3>Fresh central data</h3>
          <p class="body-md" style="margin-top: 12px;">Card and merchant rules can be updated centrally without asking every user to reinstall.</p>
        </article>
        <article class="feature-card">
          <div class="feature-icon">&check;</div>
          <h3>Honest caveats</h3>
          <p class="body-md" style="margin-top: 12px;">Where a rule is time-sensitive or merchant-specific, the answer surfaces what needs to be true.</p>
        </article>
        <article class="feature-card">
          <div class="feature-icon">&check;</div>
          <h3>MCP-ready</h3>
          <p class="body-md" style="margin-top: 12px;">Exposes a hosted Streamable HTTP MCP endpoint at kiasumiles.space/mcp.</p>
        </article>
      </div>
    </section>

    <section class="section">
      <div class="examples-panel">
        <div class="examples-grid">
          <div>
            <p class="label">Examples</p>
            <h2 style="font-size: clamp(36px, 6vw, 70px);">Real questions. Wallet-aware answers.</h2>
          </div>
          <div class="examples-list">
            <div class="example">
              <div class="question">"Best card at NTUC FairPrice?"</div>
              <div class="example-row"><div class="example-answer">UOB Preferred Platinum Visa</div><div class="example-note">4 mpd · S\$600 cap/mo</div></div>
            </div>
            <div class="example">
              <div class="question">"Which card for Grab rides?"</div>
              <div class="example-row"><div class="example-answer">KrisFlyer UOB</div><div class="example-note">1.2 mpd · MCC 7399, no bonus tier</div></div>
            </div>
            <div class="example">
              <div class="question">"SIA tickets online?"</div>
              <div class="example-row"><div class="example-answer">KrisFlyer UOB</div><div class="example-note">2.4 mpd · KrisFlyer redemptions</div></div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="section">
      <div class="final-cta">
        <div class="glow-one"></div>
        <div class="glow-two"></div>
        <div class="final-content">
          <p class="label" style="color: rgba(255,255,255,0.68);">Try it</p>
          <h2>Guess less. Tap better.</h2>
          <p class="body-lg" style="margin-top: 26px;">
            Connect your agent to the hosted MCP endpoint, pass the user's current card stack with each request, and let KiasuMiles answer before the tap.
          </p>
          <div class="final-actions">
            <a class="button button-light" href="/mcp">Open MCP endpoint</a>
            <a class="button button-outline" href="https://github.com/hosanxiv/kiasumiles" rel="noreferrer">View on GitHub</a>
          </div>
          <p class="meta-line">Data version: {data_version} &middot; Cards: {cards} &middot; Merchants: {merchants}</p>
        </div>
      </div>
    </section>
  </main>
</body>
</html>"""
