# Contact button and page

The main README already includes this button. Reuse it elsewhere if needed:

```html
<a href="https://snuffy420.github.io/MixLogic/docs/contact.html"><img src="assets/contact-button.svg" width="250" height="48" alt="Contact the MixLogic developer"></a>
```

The page is docs/contact.html. It uses MixLogic's cyan/green logo and theme, the public Formspree endpoint https://formspree.io/f/myeekrpy, and the subject MixLogic contact. No custom-build offering is included.

Enable GitHub Pages after uploading the clean source tree: Settings → Pages → Deploy from a branch → main → /(root). Keep docs/contact.html, assets/mixlogic.png and .nojekyll at their included paths. The resulting page is https://snuffy420.github.io/MixLogic/docs/contact.html.

The form has email/message validation, a hidden spam field, character count, disabled duplicate-submit handling, a timeout, and readable success/error text. With JavaScript off, its normal HTML POST opens Formspree's confirmation flow. The recipient and allowed domain must be configured in your Formspree account. No real message was sent during testing.

See [Publishing](PUBLISHING.md) for the upload checklist. Form processing follows [Formspree's AJAX documentation](https://help.formspree.io/articles/building-your-form/submit-forms-with-javascript-ajax/).
