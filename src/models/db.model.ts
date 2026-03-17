import mongoose from "mongoose"

const initDb = () => {
    mongoose.connect("mongodb://100.71.52.17:27017/netCare")
    .then(() => {
        console.log("Connected to db")
    })
    .catch( err => {
        console.log(err);
    })
}

export default initDb ;