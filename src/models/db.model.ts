import mongoose from "mongoose"

const initDb = () => {
    mongoose.connect("mongodb://adi-makdasi.tail2be12f.ts.net:27017/netCare")
    .then(() => {
        console.log("Connected to db")
    })
    .catch( err => {
        console.log(err);
    })
}

export default initDb ;