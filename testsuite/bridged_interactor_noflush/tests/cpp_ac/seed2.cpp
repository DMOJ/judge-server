#include <bits/stdc++.h>

using namespace std;

int main(int argc, const char *argv[]) {
  cin.tie(0);
  cin.sync_with_stdio(0);
  long long low = 1, high = 2000000000;
  while (low <= high) {
    long long mid = (low + high) / 2;
    cout << mid << endl;
    string res;
    cin >> res;
    if (res == "OK")
      return 0;
    else if (res == "FLOATS")
      high = mid - 1;
    else
      low = mid + 1;
  }
  cout << low << endl;
  return 0;
}
