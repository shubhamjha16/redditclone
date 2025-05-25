const express = require('express');
const mongoose = require('mongoose');
const session = require('express-session');
const MongoStore = require('connect-mongo');
const passport = require('passport');
const path = require('path');
const flash = require('connect-flash');
const methodOverride = require('method-override');
const helmet = require('helmet');
require('dotenv').config();

// Import routes
const indexRoutes = require('./routes/index');
const authRoutes = require('./routes/auth');
const collegeRoutes = require('./routes/college'); 
const postRoutes = require('./routes/post');
const commentRoutes = require('./routes/comment');
const userRoutes = require('./routes/user');
const courseRoutes = require('./routes/course');
const eventRoutes = require('./routes/event');
const studygroupRoutes = require('./routes/studygroup');

// Passport config
require('./config/passport')(passport);

const app = express();

// Connect to MongoDB
mongoose.connect(process.env.MONGO_URI, {
  useNewUrlParser: true,
  useUnifiedTopology: true,
})
.then(() => console.log('MongoDB Connected'))
.catch(err => console.log(err));

// View engine setup
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// Middleware
app.use(helmet({
  contentSecurityPolicy: false, // Configure properly in production
}));
app.use(express.static(path.join(__dirname, 'public')));
app.use(express.urlencoded({ extended: false }));
app.use(express.json());
app.use(methodOverride('_method'));
app.use(flash());

// Session config
app.use(session({
  secret: process.env.SESSION_SECRET,
  resave: false,
  saveUninitialized: false,
  store: MongoStore.create({ mongoUrl: process.env.MONGO_URI }),
  cookie: { 
    maxAge: 1000 * 60 * 60 * 24 // 1 day
  }
}));

// Passport middleware
app.use(passport.initialize());
app.use(passport.session());

// Global variables
app.use((req, res, next) => {
  res.locals.currentUser = req.user;
  res.locals.success_msg = req.flash('success_msg');
  res.locals.error_msg = req.flash('error_msg');
  res.locals.error = req.flash('error');
  next();
});

// Routes
app.use('/', indexRoutes);
app.use('/auth', authRoutes);
app.use('/colleges', collegeRoutes);
app.use('/posts', postRoutes);
app.use('/comments', commentRoutes);
app.use('/users', userRoutes);
app.use('/courses', courseRoutes);
app.use('/events', eventRoutes);
app.use('/studygroups', studygroupRoutes);

// 404 handler
app.use((req, res) => {
  res.status(404).render('error/404');
});

// Error handler
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).render('error/500');
});

const PORT = process.env.PORT || 5000;

app.listen(PORT, () => console.log(`Server started on port ${PORT}`));

module.exports = app;