"""
Parse the mhchem (https://www.ctan.org/pkg/mhchem) input (and try to give a standard LaTeX output)

Grammar:

```
SPACE := ' ';
BSLASH := '\' ;
LCB := '{' ;
RCB := '}' ;
LSB := '[' ;
RSB := ']' ;
LB := '(' ;
RB := ')' ;
DOWN := '_' ;
UP := '^' ;
PLUS := '+' ;
MINUS := '-' ;
DOT := '.' ;
STAR := '*' ;
DOLLAR := '$' ;

esc_LCB := BSLASH LCB;
es_RCB := BSLASH RSB;

empty := LCB RCB ;

DIGIT := '0' | '1' | '2' | '3' | '4' | '5' | '6' | '7' | '8' | '9' ;
number := DIGIT* ;

math := DOLLAR CHAR* DOLLAR

atom_name := uppercase_char lowercase_char? ;

implicit_number := ((LCB ((MINUS? number) | math) RCB) | (MINUS? number) | math) ;

mass_number := UP implicit_number ;
atomic_number := DOWN implicit_number ;
index := number | (DOWN implicit_number) ;
charge_or_radical := number? DOT? (PLUS | MINUS)
charge := PLUS | MINUS | (UP LCB charge_or_radical RCB) ;

bond := MINUS | '=' | '#' ;

atom := bond? mass_number? atomic_number? atom_name index? charge?
group := ((LB atom* RB) | (LSB atom* RSB) | (esc_LCB atom* esc_RCB)) index? charge? ;

stoechiometry := NUMBER ('/' NUMBER)? SPACE* ;

molecule := (atom | group)* ((DOT | STAR) molecule)? ;

state := ((LB CHAR* RB) | (DOWN LCB CHAR* RCB))? (SPACE ('v' | '^'))? ;
equation_element := stoechiometry? molecule empty? state? ;

arrow_def := "->" | "<-" | "<->" | "<-->" | "<=>" | "<<=>" | "<=>>" ;
arrow := arrow_def ((LSB (molecule | math | (LB CHAR* RCB)) RSB) (LSB (molecule | math | (LB CHAR* RCB)) RSB)?)? ;

equation_operator := PLUS | arrow ;
equation := equation_element (SPACE equation_operator SPACE equation) ;

mchem := equation? EOF ;
```
"""