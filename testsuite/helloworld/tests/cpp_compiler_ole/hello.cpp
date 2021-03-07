#define A(x) x##x##x##x
#define B(x) A(x##x##x##x)
#define C(x) B(x##x##x##x)
#define D(x) C(x##x##x##x)
#define E(x) D(x##x##x##x)
#define F(x) E(x##x##x##x)
#define G(x) F(x##x##x##x)
#define H(x) G(x##x##x##x)
#define I(x) H(x##x##x##x)
#define J(x) I(x##x##x##x)
#define K(x) J(x##x##x##x)
int main() { int x = K(a); }
