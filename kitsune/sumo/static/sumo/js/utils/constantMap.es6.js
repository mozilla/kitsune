class Constant {
  constructor(name) {
    this.name = name;
  }

  toString() {
    return this.name;
  }
}

export default function constantMap(names) {
  let constants = {};
  for (let name of names) {
    constants[name] = new Constant(name);
  }
  return constants;
}
