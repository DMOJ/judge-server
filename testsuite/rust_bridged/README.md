This test checks the shared target functionality of Rust, by having a
submission and checker in Rust. The first case always runs fine, since the
checker will not be compiled until after the submission is run. The second case
will IR if the submission and checker have misconfigured target directories.
