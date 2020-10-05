# tex2utf

This repo is a UTF8 massaging of the `tex2mail` tool for converting LaTeX to plain text, hosten at https://ctan.org/pkg/tex2mail.

Have some screenshots that show off the different (note that these are images, because the font used for Github code blocks is almost certainly not a true monospace font).

## LaTeX

Let's compare the result for the following (nonsense) LaTeX code:

```
\[
    \prod_{i=0}^n
    \Delta
    \int_{0}^{z}\sqrt{ \left (dx/dt \right )^2+\left (dy/dt \right )^2} dt
    \simeq
    \frac{z}{2} \cdot
    \left \{
        f^{(\Pi e)^i}
        \left [
            \frac{z}{2} \cdot \left ( \frac{-1}{\sqrt{3}} + \frac{z}{2} \right )
        \right ]
        + f
        \left <
            \frac{z}{2} \cdot \frac{1}{\sqrt{3}} + \frac{z}{2}
        \right >
    \right \}
\]
```

## text2mail result

<img width="866" alt="Screen Shot 2020-10-04 at 10 34 11 PM" src="https://user-images.githubusercontent.com/177243/95043598-1e672480-0692-11eb-920a-b8d55486d91d.png">

## tex2utf result

<img width="741" alt="Screen Shot 2020-10-04 at 10 34 21 PM" src="https://user-images.githubusercontent.com/177243/95043610-24f59c00-0692-11eb-9835-3de1f71ab11c.png">

(I'd love to clean up that horrible angle bracket, but I don't currently use them in any LaTeX I need converted at the moment)
