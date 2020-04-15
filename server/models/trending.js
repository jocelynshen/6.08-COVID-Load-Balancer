const mongoose = require("mongoose");

const TrendingSchema = new mongoose.Schema({
  city: String,
  country: String,
  popularity: Number,
  coordinates: []
});

module.exports = mongoose.model("trending", TrendingSchema);
