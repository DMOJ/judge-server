program aplusb;

var
n, i : longint;
a, b : longint;

begin
readln (n);
for i := 1 to n do
begin
    readln (a,b);
    writeln (a+b);
end;

end.