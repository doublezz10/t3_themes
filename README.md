# t3_themes

Custom themes for T3 Code. Each folder holds one theme.

| Theme | Preview |
| --- | --- |
| [Deep Sea](deep-sea/): 16 dot-matrix sea animals take turns swimming behind the chat | ![Deep Sea](deep-sea/preview/home.gif) |

## Installing a theme

T3 Code themes are applied through its built-in theme tool, so the easiest way is to ask the agent in a T3 Code thread:

> Apply the T3 theme in `deep-sea/theme.json` from this repo, with theme id `deep-sea`.

`theme.json` is the full object the tool expects: name, appearance, base colors, and custom CSS. To undo, switch back to a built-in theme such as `t3-chat` or `ocean`.

Themes apply to the desktop and web apps. The T3 mobile app does not use custom themes.

## Repo layout

```
<theme-name>/
  theme.json      # the theme as T3 applies it (generated)
  theme.css       # the theme's custom CSS alone (generated)
  generate.py     # source; edit this, then run it to rebuild the files above
  preview/        # screenshots and GIFs for the README
```

## Limits worth knowing

- A theme's custom CSS can be at most 20,000 characters.
- CSS cannot load files, so images have to be embedded as `data:` URLs.
- Only the stable selectors T3 documents (such as `[data-workspace-area="conversation"]`) are safe to target; other class names change between releases.

## License

MIT. See [LICENSE](LICENSE).
