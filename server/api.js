/*
|--------------------------------------------------------------------------
| api.js -- server routes
|--------------------------------------------------------------------------
|
| This file defines the routes for your server.
|
*/

const express = require("express");

const Answer = require("./models/answer");
const Question = require("./models/question");
const Response = require("./models/response");
const User = require("./models/user");
const Trending = require("./models/trending")
const mongoose = require("mongoose");

const authentication = require("./auth");

require("dotenv").config();

const router = express.Router();

router.post("/response", (req, res) => {
  let userResponse = req.body.responseAnswers, userScore = req.body.numCorrect, userTotal = req.body.numTotal, responses = [];
  for (let i = 0; i < userResponse.length; i++) {
    const jsonObject = userResponse[i];
    const newResponse = new Response({
      responseUserId: req.user._id,
      responseAnswer: jsonObject.responseAnswerId,
      responseQuestion: jsonObject.responseQuestionId,
      answerText: jsonObject.freeResponseAnswer,
      inLocation: jsonObject.inLocation,
		date: new Date(),

    });
    responses.push(newResponse);
    console.log("responses that still exist", responses)
  }

  let bulkOps = [];
  for (let i = 0; i < responses.length; i++) {
    let questionId = responses[i].responseQuestion, answerId = responses[i].responseAnswer, answerText = responses[i].answerText;
    let upsertDoc = {
      updateOne: {
        filter: {_id: mongoose.Types.ObjectId(questionId),"answers._id": mongoose.Types.ObjectId(answerId)},
        update: { $inc: {"answers.$.countIn": responses[i].inLocation ? 1 : 0} }
      }
    };
    let upsertDoc2 = {
      updateOne: {
        filter: {_id: mongoose.Types.ObjectId(questionId),"answers._id": mongoose.Types.ObjectId(answerId)},
        update: { $inc: {"answers.$.countOut": responses[i].inLocation ? 0 : 1} }
      }
    };
    let upsertDocFreeResponse = {
        updateOne: {filter: { _id: mongoose.Types.ObjectId(questionId) },
        update: { $push: { freeResponseAnswers: answerText } }
      }
    };
    bulkOps.push(upsertDoc);
    bulkOps.push(upsertDoc2)
    bulkOps.push(upsertDocFreeResponse);
  }

  User.findOneAndUpdate({ _id: req.user._id },{ $inc: { correct: userScore, total_answered: userTotal }, $push: { answeredQuestions: { $each: responses } } },{ new: true }, // update profile total score
    function(err, response) {
      Question.bulkWrite(bulkOps).then(response2 => { // update counts and free response answers
        res.send(response2);
      });
    }
  );
});

router.get("/questions", (req, res) => {
  let lat = req.query.lat, lng = req.query.lng;
  User.findById(req.user._id).then(user => {
    let answeredQuestions = user.answeredQuestions.map(obj => {return mongoose.Types.ObjectId(obj.responseQuestion);});
    Question.findRandom({
        questionLocation: { $near: {$maxDistance: req.query.searchRadius,$geometry: {type: "Point",coordinates: [lng, lat]}}},
        creator_id: {$ne: req.user._id},
        _id: { $nin: answeredQuestions }
      },
      {},
      { limit: 5 },
      function(err, results) {if (!err) {if (!results) {res.send([]);} else {res.json(results);}} else {console.log(err);}}
    );
  });
});

router.post("/question", (req, res) => {
  let arr = req.body.answers;
  let answerObjects = [];
  for (let i = 0; i < arr.length; i++) {
    answerObjects.push(
      new Answer({
        answer: arr[i].answer,
        answerType: arr[i].answerType,
        city: req.body.city,
        country: req.body.country,
        countIn: 0,
        countOut: 0
      })
    );
  }
  const newQuestion = new Question({
    creator_id: req.user._id,
    date: new Date(),
    questionLocation: {
      type: "Point",
      coordinates: [req.body.lng, req.body.lat]
    },
    question: req.body.question,
    answers: answerObjects,
    freeResponseAnswers: [],
    allowFreeResponse: req.body.freeResponse
  });
  newQuestion.save().then(question => {
    User.update({ _id: req.user._id },{ $push: { postedQuestions: question._id } },function(err) {if (err) {console.log(err);} else {res.send(question);}});
  });
});

router.get("/user", (req, res) => {
  User.findById(req.query.userid).then(user => {
    res.send(user);
  });
});

router.post("/updatepermissions", (req, res) => {
  User.update({ _id: req.user._id }, { $set: { locationPermissions: req.body.locationPermissions, firstTimeUser: false} },{ multi: true }, function(err) {
    res.send({})
   });
})

router.get("/correct", (req, res) => {
  User.findById(req.query.userid).then(user => {
    res.send(user.correct.toString(10));
  });
});

router.get("/total", (req, res) => {
  User.findById(req.query.userid).then(user => {
    res.send(user.total_answered.toString(10));
  });
});

router.post("/trending", (req, res) => {
  Trending.findOneAndUpdate({city: req.body.city ? req.body.city: "", country: req.body.country ? req.body.country: ""}, {$inc: {popularity: 1}, $set: {coordinates: [req.body.lat, req.body.lng]}}, { upsert: true, new: true, setDefaultsOnInsert: true }, function(err, result) {
    res.send(result)
  })
})

router.get("/trends", (req, res) => {
  Trending.find({}).sort({popularity: -1}).limit(10).exec(
    function(err, places) {
      res.send(places)
  })
})

router.post("/login", authentication.login);

router.post("/logout", authentication.logout);

router.get("/whoami", (req, res) => {
  if (req.user) {
    res.send(req.user);
  } else {
    res.send({});
  }
});

//for profile
router.get("/userAnswersId", (req, res) => {
  User.findById(req.user._id).then(user => {
    let ids = user.answeredQuestions.map((obj) => {
		return Question.findById(mongoose.Types.ObjectId(obj.responseQuestion)).exec()
	}).reverse()

	Promise.all(ids).then(function(values) {
    console.log(values)
		res.send(values.filter((val) => {return val !== null}))
	})
})});

router.get("/userPostedId", (req, res) => {
  User.findById(req.user._id).then(user => {
    let postedIds = user.postedQuestions.map((obj) => {return mongoose.Types.ObjectId(obj)});
    Question.find({'_id': {
      $in: postedIds
    }}).sort({'date': 'desc'}).exec(function(err, docsAnswered) {
      res.send(docsAnswered)
    })
  })});

router.all("*", (req, res) => {
  console.log(`API route not found: ${req.method} ${req.url}`);
  res.status(404).send({ msg: "API route not found" });
});

module.exports = router;
