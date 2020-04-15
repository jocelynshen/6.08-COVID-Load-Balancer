const mongoose = require("mongoose");

const UserSchema = new mongoose.Schema({
  name: String,
  googleid: String,
  correct: Number,
  total_answered: Number,
  answeredQuestions: [],
  postedQuestions: [],
  locationPermissions: Boolean,
  firstTimeUser: Boolean
});

// compile model from schema
module.exports = mongoose.model("user", UserSchema);
