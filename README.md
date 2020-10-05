# Tex2utf

This repo is a UTF8 massaging of the `tex2mail` tool (with some fixes around how brackets are constructed) for converting LaTeX maths to an easier to read, plain text form (for use in contexts that don't support graphical rendering).

The original can be found over on https://ctan.org/pkg/tex2mail.

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

## tex2mail result

<img width="866" alt="Screen Shot 2020-10-04 at 10 34 11 PM" src="https://user-images.githubusercontent.com/177243/95043598-1e672480-0692-11eb-920a-b8d55486d91d.png">

## tex2utf result

<img width="741" alt="Screen Shot 2020-10-04 at 10 34 21 PM" src="https://user-images.githubusercontent.com/177243/95043610-24f59c00-0692-11eb-9835-3de1f71ab11c.png">

(I'd like to clean up that horrible angle bracket, but I don't currently use them in any LaTeX I need converted, so I'm in no rush)

## Todo's

I'd honestly love to get this turned into a Python script, because Perl programmers are a dying breed (I haven't worked with Perl in 20 years, so I spent way more time than I would have liked relearning how everything works) and having functions with actual named parameters is kind of nice if you want folks to understand what's going on and possibly help improve the code.

That said, if you feel this is something that can (finally) do what you need, and it's doing something wrong, and you know how to fix it (or you know where it's going wrong even if you don't know exactly how to fix it): file an issue, or even a PR, and let's get this tool updated to modern standards!
