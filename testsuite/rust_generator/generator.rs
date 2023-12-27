use rand::{Rng, SeedableRng};

type ConcreteRng = rand_xoshiro::Xoshiro256PlusPlus;

fn main() {
    let mut args = std::env::args();
    args.next();
    let mut rng = ConcreteRng::seed_from_u64(args.next().unwrap().parse().unwrap());

    let x = rng.gen_range(0..10);
    let y = rng.gen_range(0..10);
    println!("{x} {y}");
    eprintln!("{}", x + y);
}
