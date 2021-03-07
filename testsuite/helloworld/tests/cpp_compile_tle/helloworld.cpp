#define a(x) 1;
#define b(x)                                                                   \
  a(x) a(x) a(x) a(x) a(x) a(x) a(x) a(x) a(x) a(x) a(x) a(x) a(x) a(x) a(x)   \
      a(x) a(x) a(x) a(x) a(x) a(x) a(x) a(x) a(x) a(x) a(x) a(x) a(x) a(x)    \
          a(x) a(x) a(x) a(x) a(x) a(x) a(x) a(x) a(x) a(x) a(x) a(x) a(x)     \
              a(x) a(x) a(x) a(x) a(x) a(x) a(x)
#define c(x)                                                                   \
  b(x) b(x) b(x) b(x) b(x) b(x) b(x) b(x) b(x) b(x) b(x) b(x) b(x) b(x) b(x)   \
      b(x) b(x) b(x) b(x) b(x) b(x) b(x) b(x) b(x) b(x) b(x) b(x) b(x) b(x)    \
          b(x) b(x) b(x) b(x) b(x) b(x) b(x) b(x) b(x) b(x) b(x) b(x) b(x)     \
              b(x) b(x) b(x) b(x) b(x) b(x) b(x)
#define d(x)                                                                   \
  c(x) c(x) c(x) c(x) c(x) c(x) c(x) c(x) c(x) c(x) c(x) c(x) c(x) c(x) c(x)   \
      c(x) c(x) c(x) c(x) c(x) c(x) c(x) c(x) c(x) c(x) c(x) c(x) c(x) c(x)    \
          c(x) c(x) c(x) c(x) c(x) c(x) c(x) c(x) c(x) c(x) c(x) c(x) c(x)     \
              c(x) c(x) c(x) c(x) c(x) c(x) c(x)
#define e(x)                                                                   \
  d(x) d(x) d(x) d(x) d(x) d(x) d(x) d(x) d(x) d(x) d(x) d(x) d(x) d(x) d(x)   \
      d(x) d(x) d(x) d(x) d(x) d(x) d(x) d(x) d(x) d(x) d(x) d(x) d(x) d(x)    \
          d(x) d(x) d(x) d(x) d(x) d(x) d(x) d(x) d(x) d(x) d(x) d(x) d(x)     \
              d(x) d(x) d(x) d(x) d(x) d(x) d(x)
#define f(x)                                                                   \
  e(x) e(x) e(x) e(x) e(x) e(x) e(x) e(x) e(x) e(x) e(x) e(x) e(x) e(x) e(x)   \
      e(x) e(x) e(x) e(x) e(x) e(x) e(x) e(x) e(x) e(x) e(x) e(x) e(x) e(x)    \
          e(x) e(x) e(x) e(x) e(x) e(x) e(x) e(x) e(x) e(x) e(x) e(x) e(x)     \
              e(x) e(x) e(x) e(x) e(x) e(x) e(x)
#define g(x)                                                                   \
  f(x) f(x) f(x) f(x) f(x) f(x) f(x) f(x) f(x) f(x) f(x) f(x) f(x) f(x) f(x)   \
      f(x) f(x) f(x) f(x) f(x) f(x) f(x) f(x) f(x) f(x) f(x) f(x) f(x) f(x)    \
          f(x) f(x) f(x) f(x) f(x) f(x) f(x) f(x) f(x) f(x) f(x) f(x) f(x)     \
              f(x) f(x) f(x) f(x) f(x) f(x) f(x)
#define h(x)                                                                   \
  g(x) g(x) g(x) g(x) g(x) g(x) g(x) g(x) g(x) g(x) g(x) g(x) g(x) g(x) g(x)   \
      g(x) g(x) g(x) g(x) g(x) g(x) g(x) g(x) g(x) g(x) g(x) g(x) g(x) g(x)    \
          g(x) g(x) g(x) g(x) g(x) g(x) g(x) g(x) g(x) g(x) g(x) g(x) g(x)     \
              g(x) g(x) g(x) g(x) g(x) g(x) g(x)
#define i(x)                                                                   \
  h(x) h(x) h(x) h(x) h(x) h(x) h(x) h(x) h(x) h(x) h(x) h(x) h(x) h(x) h(x)   \
      h(x) h(x) h(x) h(x) h(x) h(x) h(x) h(x) h(x) h(x) h(x) h(x) h(x) h(x)    \
          h(x) h(x) h(x) h(x) h(x) h(x) h(x) h(x) h(x) h(x) h(x) h(x) h(x)     \
              h(x) h(x) h(x) h(x) h(x) h(x) h(x)
#define j(x)                                                                   \
  i(x) i(x) i(x) i(x) i(x) i(x) i(x) i(x) i(x) i(x) i(x) i(x) i(x) i(x) i(x)   \
      i(x) i(x) i(x) i(x) i(x) i(x) i(x) i(x) i(x) i(x) i(x) i(x) i(x) i(x)    \
          i(x) i(x) i(x) i(x) i(x) i(x) i(x) i(x) i(x) i(x) i(x) i(x) i(x)     \
              i(x) i(x) i(x) i(x) i(x) i(x) i(x)
#define k(x)                                                                   \
  j(x) j(x) j(x) j(x) j(x) j(x) j(x) j(x) j(x) j(x) j(x) j(x) j(x) j(x) j(x)   \
      j(x) j(x) j(x) j(x) j(x) j(x) j(x) j(x) j(x) j(x) j(x) j(x) j(x) j(x)    \
          j(x) j(x) j(x) j(x) j(x) j(x) j(x) j(x) j(x) j(x) j(x) j(x) j(x)     \
              j(x) j(x) j(x) j(x) j(x) j(x) j(x)
#define l(x)                                                                   \
  k(x) k(x) k(x) k(x) k(x) k(x) k(x) k(x) k(x) k(x) k(x) k(x) k(x) k(x) k(x)   \
      k(x) k(x) k(x) k(x) k(x) k(x) k(x) k(x) k(x) k(x) k(x) k(x) k(x) k(x)    \
          k(x) k(x) k(x) k(x) k(x) k(x) k(x) k(x) k(x) k(x) k(x) k(x) k(x)     \
              k(x) k(x) k(x) k(x) k(x) k(x) k(x)
int main() {
  l(x);
  return -1;
}
