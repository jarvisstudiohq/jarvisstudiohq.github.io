/*
 * Jarvis Studios website settings.
 *
 * supportEmail is THE ONE PLACE the support email is set. Every page shows it from here.
 * After changing it, run `python3 tools/build.py` so the pages also carry it for visitors without JavaScript,
 * then `python3 tools/check.py`.
 */
window.SITE_CONFIG = {
  supportEmail: "jarvisstudiohq@gmail.com",

  /*
   * Optional. The published address of the site, ending in "/", for example
   * "https://jarvisstudio.github.io/" or "https://cjarvis0.github.io/jarvis-studio/".
   * Leave it empty: every link on the site is relative, so the site works at any address.
   * Only the 404 page uses it, as a shortcut for finding the home page.
   */
  siteUrl: "https://jarvisstudiohq.github.io/"
};
