package TeXDefinitions;

use strict;
use warnings;
no strict 'vars';  # Allow old-style local variables
use utf8;
use Tex2UtfConfig;
use MacroExpansion;

use Exporter 'import';
our @EXPORT = qw(initialize_definitions);

sub initialize_definitions {

  $type{"\\sum"}="record";
  $contents{"\\sum"}="3,3,1,0," . <<'EOF';
__
❯
‾‾
EOF

  $type{"\\int"}="record";
  $contents{"\\int"}="3,3,1,0," . <<'EOF';
 ╭
 |
 ╯
EOF

  $type{"\\prod"}="record";
  $contents{"\\prod"}="2,3,1,0," . <<'EOF';
___
│ │
EOF

  $type{"\\Sigma"}="record";
  $contents{"\\Sigma"}="3,2,1,0," . <<'EOF';
__
❯
‾‾
EOF

  $type{"\\textit"}="string";
  $contents{"\\textit"}=" ";

  $type{"\\oplus"}="string";
  $contents{"\\oplus"}="⊕";

  $type{"\\otimes"}="string";
  $contents{"\\otimes"}="⊗";

  $type{"\\ominus"}="string";
  $contents{"\\ominus"}="⊖";

  $type{"\\leq"}="string";
  $contents{"\\leq"}="≤";

  $type{"\\equiv"}="string";
  $contents{"\\equiv"}="≡";

  $type{"\\geq"}="string";
  $contents{"\\geq"}="≥";

  $type{"\\partial"}="string";
  $contents{"\\partial"}="∂";

  $type{"\\forall"}="string";
  $contents{"\\forall"}="∀";

  $type{"\\exists"}="string";
  $contents{"\\exists"}="∃";

  $type{"\\owns"}="string";
  $contents{"\\owns"}="∋";

  $type{"\\ni"}="string";
  $contents{"\\ni"}="∌";

  $type{"\\in"}="string";
  $contents{"\\in"}="∈";

  $type{"\\notin"}="string";
  $contents{"\\notin"}="∉";

  $type{"\\qed"}="string";
  $contents{"\\qed"}="∎";

  $type{"\\pm"}="string";
  $contents{"\\pm"}="±";

  $type{"\\mp"}="string";
  $contents{"\\mp"}="∓";

  $type{"\\cong"}="string";
  $contents{"\\cong"}="≅";

  $type{"\\neq"}="string";
  $contents{"\\neq"}="≠";

  $type{"\\nmid"}="string";
  $contents{"\\nmid"}="∤";

  $type{"\\subset"}="string";
  $contents{"\\subset"}="⊂";

  $type{"\\subseteq"}="string";
  $contents{"\\subseteq"}="⊆";

  $type{"\\supseteq"}="string";
  $contents{"\\subseteq"}="⊇";

  $type{"\\supset"}="string";
  $contents{"\\supset"}="⊃";

  $type{"\\sqrt"}="sub1";
  $contents{"\\sqrt"}="radical";

  $type{"\\buildrel"}="sub3";
  $contents{"\\buildrel"}="buildrel";

  $type{"\\frac"}="sub2";
  $contents{"\\frac"}="fraction";

  $type{"\\LITERALnoLENGTH"}="sub1";
  $contents{"\\LITERALnoLENGTH"}="literal_no_length";

  for ("text","operatorname","operatornamewithlimits","relax","-",
       "notag","!","/","protect","mathcal","Bbb","bf","it","em","boldsymbol",
       "cal","Cal","goth","ref","maketitle","expandafter","csname","endcsname",
       "makeatletter","makeatother","topmatter","endtopmatter","rm",
       "NoBlackBoxes","document","TagsOnRight","bold","dsize","roster",
       "endroster","endkey","endRefs","enddocument","displaystyle",
       "twelverm","tenrm","twelvefm","tenfm","hbox","mbox") {
    $type{"\\$_"}="nothing";
  }
  for ("par","endtitle","endauthor","endaffil","endaddress","endemail",
       "endhead","key","medskip","smallskip","bigskip","newpage",
       "vfill","eject","endgraph") {
    $type{"\\$_"}="sub";
    $contents{"\\$_"}="par";
  }

  for ("proclaim","demo",) {
    $type{"\\$_"}="par_self";
  }

  for ("endproclaim","enddemo",) {
    $type{"\\$_"}="self_par";
  }

  $type{"\\let"}="sub";
  $contents{"\\let"}="let_exp";

  $type{"\\def"}="sub";
  $contents{"\\def"}="def_exp";

  $type{"\\item"}="sub";
  $contents{"\\item"}="item";

  $type{"{"}="sub";
  $contents{"{"}="open_curly";

  $type{"}"}="sub";
  $contents{"}"}="close_curly";

  $type{"&"}="sub";
  $contents{"&"}="ampersand";

  $type{'$'}="sub";
  $contents{'$'}="dollar";

  $type{'$$'}="sub";
  $contents{'$$'}="ddollar";

  $type{'\\\\'}="sub";
  $contents{'\\\\'}="bbackslash";

  $type{"^"}="sub1";
  $contents{"^"}="superscript";

  $type{"_"}="sub1";
  $contents{"_"}="subscript";

  $type{"@"}="sub";
  $contents{"@"}="at";

  $type{"\\over"}="sub";
  $contents{"\\over"}="over";

  $type{"\\choose"}="sub";
  $contents{"\\choose"}="choose";

  $type{"\\noindent"}="sub";
  $contents{"\\noindent"}="noindent";

  $type{"\\left"}="sub";
  $contents{"\\left"}="left";

  $type{"\\right"}="sub";
  $contents{"\\right"}="right";

  $type{"\\underline"}="sub1";
  $contents{"\\underline"}="underline";

  $type{"\\overline"}="sub1";
  $contents{"\\overline"}="overline";

  $type{"\\bar"}="sub1";
  $contents{"\\bar"}="overline";

  $type{"\\v"}="sub1";
  $contents{"\\v"}="putover_string;v";

  $type{"\\widetilde"}="sub1";
  $contents{"\\widetilde"}="widetilde";

  $type{"\\~"}="sub1";
  $contents{"\\~"}="putover_string;~";

  $type{"\\tilde"}="sub1";
  $contents{"\\tilde"}="putover_string;~";

  $type{"\\widehat"}="sub1";
  $contents{"\\widehat"}="widehat";

  $type{"\\hat"}="sub1";
  $contents{"\\hat"}="putover_string;^";

  $type{"\\^"}="sub1";
  $contents{"\\^"}="putover_string;^";

  $type{'\\"'}="sub1";
  $contents{'\\"'}='putover_string;"';

  $type{'\\dot'}="sub1";
  $contents{'\\dot'}='putover_string;.';

  $type{"\\not"}="sub1";
  $contents{"\\not"}="not";

  $type{"\\label"}="sub1";
  $contents{"\\label"}="putpar;(;)";

  $type{"\\eqref"}="sub1";
  $contents{"\\eqref"}="putpar;(;)";

  $type{"\\cite"}="sub1";
  $contents{"\\cite"}="putpar;[;]";

  $type{"\\begin"}="sub1";
  $contents{"\\begin"}="begin";

  $type{"\\end"}="sub1";
  $contents{"\\end"}="end";

  for ('@',"_","\$","{","}","#","&","arccos","arcsin","arctan","arg","cos",
      "cosh","cot","coth","csc","deg","det","dim","exp","gcd","hom",
      "inf","ker","lg","lim","liminf","limsup","ln","log","max","min",
      "mod","Pr","sec","sin","sinh","sup","tan","tanh", "%") {
    $type{"\\$_"}="self";
  }

  for ("bibliography","myLabel","theoremstyle","theorembodyfont",
       "bibliographystyle","hphantom","vphantom","phantom","hspace") {
    $type{"\\$_"}="discard1";
  }

  for ("numberwithin","newtheorem","renewcommand","setcounter"
      ) {
    $type{"\\$_"}="discard2";
  }

  for ("equation","gather","align"
       ) {$environment{"$_"}="ddollar,ddollar";}

  for ("matrix","CD","smallmatrix"
       ) {$environment{"$_"}="matrix,endmatrix;1;c";}

  for ("document","split","enumerate"
       ) {$environment_none{"$_"}++;}

  $environment{"Sb"}="subscript:matrix,endmatrix;1;l";

  $environment{"Sp"}="superscript:matrix,endmatrix;1;l";

  $environment{"eqnarray"}="ddollar:matrix,endmatrix;0;r;c;l:ddollar";
  $environment{"split"}="ddollar:matrix,endmatrix;0;r;l:ddollar";
  $environment{"multiline"}="ddollar:matrix,endmatrix;0;r;l:ddollar";
  $environment{"align"}="ddollar:matrix,endmatrix;0;r;l:ddollar";
  $environment{"aligned"}="matrix,endmatrix;0;r;l";
  $environment{"gather"}="ddollar:matrix,endmatrix;0;c:ddollar";
  $environment{"gathered"}="matrix,endmatrix;0;c";
  $environment{"array"}="arg2stack:matrix,endmatrixArg;1";

  $environment{"bmatrix"}="beg_lr;[;]:matrix,endmatrix;1;c";
  $environment{"vmatrix"}="beg_lr;|;|:matrix,endmatrix;1;c";

  $type{"~"}="string";
  $contents{"~"}=" ";

  $type{"\\,"}="string";
  $contents{"\\,"}=" ";

  $type{"\\dots"}="string";
  $contents{"\\dots"}="...";

  $type{"\\ldots"}="string";
  $contents{"\\ldots"}="...";

  $type{"\\cdots"}="string";
  $contents{"\\cdots"}="⋯";

  $type{"\\colon"}="string";
  $contents{"\\colon"}=": ";

  $type{"\\mid"}="string";
  $contents{"\\mid"}=" | ";

  $type{"\\smallsetminus"}="string";
  $contents{"\\smallsetminus"}=" ⧵ ";

  $type{"\\setminus"}="string";
  $contents{"\\setminus"}=" ⧹ ";

  $type{"\\backslash"}="string";
  $contents{"\\backslash"}="\\";

  $type{"\\approx"}="string";
  $contents{"\\approx"}=" ≅ ";

  $type{"\\simeq"}="string";
  $contents{"\\simeq"}=" ≃ ";

  $type{"\\quad"}="string";
  $contents{"\\quad"}="   ";

  $type{"\\qquad"}="string";
  $contents{"\\qquad"}="     ";

  $type{"\\Delta"}="string";
  $contents{"\\Delta"}="△";

  $type{"\\Pi"}="string";
  $contents{"\\Pi"}="π";

  $type{"\\alpha"}="string";
  $contents{"\\alpha"}="α";

  $type{"\\to"}="string";
  $contents{"\\to"}=" ──> ";

  $type{"\\from"}="string";
  $contents{"\\from"}=" <── ";

  $type{"\\wedge"}="string";
  $contents{"\\wedge"}="∧";

  $type{"\\Lambda"}="string";
  $contents{"\\Lambda"}="∨";

  $type{"\\ltimes"}="string";
  $contents{"\\ltimes"}="⋉";

  $type{"\\lhd"}="string";
  $contents{"\\lhd"}=" ⊲ ";

  $type{"\\rhd"}="string";
  $contents{"\\rhd"}=" ⊳ ";

  $type{"\\cdot"}="string";
  $contents{"\\cdot"}=" · ";

  $type{"\\circ"}="string";
  $contents{"\\circ"}=" o ";

  $type{"\\bullet"}="string";
  $contents{"\\bullet"}="•";

  $type{"\\infty"}="string";
  $contents{"\\infty"}="∞";

  $type{"\\rtimes"}="string";
  $contents{"\\rtimes"}=" ⋊ ";

  $type{"\\times"}="string";
  $contents{"\\times"}=" × ";

  $type{"\\hookrightarrow"}="string";
  $contents{"\\hookrightarrow"}=" ↪ ";

  $type{"\\hookleftarrow"}="string";
  $contents{"\\hookleftarrow"}=" ↩ ";

  $type{"\\longleftarrow"}="string";
  $contents{"\\longleftarrow"}=" <──── ";

  $type{"\\longleftrightarrow"}="string";
  $contents{"\\longleftrightarrow"}=" <────> ";

  $type{"\\longrightarrow"}="string";
  $contents{"\\longrightarrow"}=" ────> ";

  $type{"\\rightarrow"}="string";
  $contents{"\\rightarrow"}=" ──> ";

  $type{"\\leftarrow"}="string";
  $contents{"\\leftarrow"}=" <── ";

  $type{"\\Rightarrow"}="string";
  $contents{"\\Rightarrow"}=" ==> ";

  $type{"\\Leftarrow"}="string";
  $contents{"\\Leftarrow"}=" <== ";

  $type{"\\mapsto"}="string";
  $contents{"\\mapsto"}=" ├──> ";

  $type{"\\longmapsto"}="string";
  $contents{"\\longmapsto"}=" ├────> ";

  $type{"\\cap"}="string";
  $contents{"\\cap"}=" ∩ ";

  $type{"\\cup"}="string";
  $contents{"\\cup"}=" ∪ ";

  $type{"\\section"}="string";
  $contents{"\\section"}="Section ";

  $type{"\\subsection"}="string";
  $contents{"\\subsection"}="Subsection ";

  $type{"\|"}="string";
  $contents{"\|"}="||";

  $type{'\;'}="string";
  $contents{'\;'}=" ";

  $type{'\noindent'}="string";
  $contents{'\noindent'}="";

  &define('\\define','\\def');
  &define('\\ge','\\geq');
  &define('\\le','\\leq');
  &define('\\ne','\\neq');
  &define('\\langle','<');
  &define('\\rangle','>');
  &define('\\subheading','\\par\\underline');
  &define('\\(','$');
  &define('\\)','$');
  &define('\\[','$$');
  &define('\\]','$$');
  &define('\\centerline#1','$$#1$$');
  &define('\\eqalign#1','\\aligned #1 \\endaligned');
  &define('\\cr','\\\\');
  &define('\\sb','_');
  &define('\\sp','^');
  &define('\\proclaim','\\noindent ');

  &defb("matrix","vmatrix","Vmatrix","smallmatrix","bmatrix","Sp","Sb","CD","align","aligned","split","multiline","gather","gathered");

  if ($opt_TeX) {
    &define('\pmatrix#1','\left(\begin{matrix}#1\end{matrix}\right)');
  } else {
    $environment{"pmatrix"}="beg_lr;(;):matrix,endmatrix;1;c";
    &defb("pmatrix");
  }

  # All the records should be specified before this point
  {
    local(@a)=grep("record" eq $type{$_},keys %type);
    for (@a) {
      chop $contents{$_} if substr($contents{$_},length($contents{$_})-1,1) eq "\n";
    }
  }

  for ("oplus","otimes","cup","wedge") {
    $type{"\\big$_"}=$type{"\\$_"};
    $contents{"\\big$_"}=$contents{"\\$_"};
  }
}

1;
