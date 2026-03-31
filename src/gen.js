const crypto = require("crypto");

const hostname = "gns3vm";

const key = crypto
  .createHash("md5")
  .update(hostname + "gns3")
  .digest("hex");

console.log(key);