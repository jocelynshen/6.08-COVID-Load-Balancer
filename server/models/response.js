const mongoose = require("mongoose");

const ResponseSchema = new mongoose.Schema({
  date: Date,
  responseUserId: String,
  responseAnswer: String,
  responseQuestion: String,
  answerText: String,
  inLocation: Boolean
});

module.exports = mongoose.model("response", ResponseSchema);
