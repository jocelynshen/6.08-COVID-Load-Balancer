const mongoose = require("mongoose");

const AnswerSchema = new mongoose.Schema({
  answer: String,
  countIn: Number,
  countOut: Number,
  city: String,
  country: String,
  answerType: String,
});

module.exports = mongoose.model("answer", AnswerSchema);
