template <class T> class a { a<T *> operator->(); };
a<int> i = i->b;