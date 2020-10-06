# Tex2utf

This repo is a UTF8 massaging of the `tex2mail` tool (with some fixes around how brackets are constructed) for converting LaTeX maths to an easier to read, plain text form (for use in contexts that don't support graphical rendering).

The original can be found over on https://ctan.org/pkg/tex2mail.

## Usage

Place both `tex2utf.pl` and `newgetopts.pl` in a dir somewhere, then invoke using perl as:

```
> perl path/to/tex2utf.pl inputfile.tex
```

**Note:** because this is an update to tex2mail to support UTF8, your terminal environment must be set to utf8 encoding. If not, you're basically guaranteed to get `Wide character in print at ...` errors.


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

![](./preview-tex2mail.png)


## tex2utf result

![](./preview-tex2utf.png)


## Todo's

I'd honestly love to get this turned into a Python script, because Perl programmers are a dying breed (I haven't worked with Perl in 20 years, so I spent way more time than I would have liked relearning how everything works) and having functions with actual named parameters is kind of nice if you want folks to understand what's going on and possibly help improve the code.

That said, if you feel this is something that can (finally) do what you need, and it's doing something wrong, and you know how to fix it (or you know where it's going wrong even if you don't know exactly how to fix it): file an issue, or even a PR, and let's get this tool updated to modern standards!
