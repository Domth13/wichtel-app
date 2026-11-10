"""Gemeinsames, E-Mail-Client-freundliches Layout für Wichtel-Nachrichten."""

import html


def render_event_email(*, lang, heading, subheading, hello, event_text, detail, button, footer, url):
    """Rendert ein responsives HTML-Layout; event_text enthält vertrauenswürdiges Markup."""
    esc = lambda value: html.escape(str(value or ""), quote=True)
    language = lang if lang in ("de", "en") else "de"
    return f'''<!DOCTYPE html>
<html lang="{language}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light dark">
  <meta name="supported-color-schemes" content="light dark">
  <title>{esc(heading)}</title>
  <style>
    @media (prefers-color-scheme: dark) {{
      .mail-bg {{ background-color: #151c18 !important; }}
      .mail-card {{ background-color: #222d26 !important; border-color: #425347 !important; }}
      .mail-text {{ color: #eef3ec !important; }}
      .mail-muted {{ color: #b6c4b8 !important; }}
      .mail-brand, .mail-title, .mail-accent {{ color: #9bd7ad !important; }}
      .mail-banner {{ background-color: #294436 !important; border-color: #425347 !important; }}
      .mail-button {{ background-color: #285f40 !important; color: #ffffff !important; }}
    }}
    @media only screen and (max-width: 480px) {{
      .mail-outer {{ padding: 20px 12px !important; }}
      .mail-inner {{ padding: 26px 22px !important; }}
      .mail-title {{ font-size: 25px !important; }}
    }}
  </style>
</head>
<body class="mail-bg" style="margin:0; padding:0; background-color:#f8fbf9; color:#20332a; font-family:Arial,Helvetica,sans-serif;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" class="mail-bg" style="background-color:#f8fbf9;">
    <tr><td align="center" class="mail-outer" style="padding:32px 16px;">
      <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="max-width:560px;">
        <tr><td class="mail-brand" style="padding:0 4px 18px; color:#205d3d; font-size:15px; font-weight:bold;">🎄 Wichtel</td></tr>
        <tr><td class="mail-card" style="background-color:#ffffff; border:1px solid #dce8e0; border-radius:20px;">
          <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
            <tr><td class="mail-inner" style="padding:36px 38px;">
              <h1 class="mail-title" style="margin:0 0 20px; color:#205d3d; font-size:29px; line-height:1.2;">{esc(heading)}</h1>
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                <tr><td class="mail-banner mail-accent" style="padding:16px 18px; background-color:#e8f4ec; border:1px solid #d2e7d9; border-radius:12px; color:#205d3d; font-size:16px; font-weight:bold; line-height:1.4;">{esc(subheading)}</td></tr>
              </table>
              <p class="mail-text" style="margin:24px 0 12px; color:#20332a; font-size:16px; line-height:1.6;">{esc(hello)}</p>
              <p class="mail-text" style="margin:0 0 12px; color:#20332a; font-size:16px; line-height:1.6; overflow-wrap:anywhere;">{event_text}</p>
              <p class="mail-text" style="margin:0 0 24px; color:#20332a; font-size:16px; line-height:1.6;">{esc(detail)}</p>
              <table role="presentation" cellspacing="0" cellpadding="0" border="0"><tr>
                <td bgcolor="#205d3d" style="border-radius:10px; background-color:#205d3d;">
                  <a class="mail-button" href="{esc(url)}" style="display:inline-block; padding:14px 22px; border-radius:10px; background-color:#205d3d; color:#ffffff; font-size:15px; font-weight:bold; line-height:1.25; text-decoration:none;">{esc(button)}</a>
                </td>
              </tr></table>
              <p class="mail-muted" style="margin:28px 0 0; padding-top:20px; border-top:1px solid #dce8e0; color:#53685c; font-size:14px; line-height:1.5;">{esc(footer)}</p>
            </td></tr>
          </table>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>'''
