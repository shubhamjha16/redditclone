const mongoose = require('mongoose');
const bcrypt = require('bcryptjs');

const UserSchema = new mongoose.Schema({
  email: {
    type: String,
    required: true,
    unique: true,
    trim: true,
    lowercase: true
  },
  password: {
    type: String,
    required: true
  },
  username: {
    type: String,
    required: true,
    unique: true,
    trim: true
  },
  firstName: {
    type: String,
    trim: true
  },
  lastName: {
    type: String,
    trim: true
  },
  profileImage: {
    type: String,
    default: 'default-profile.png'
  },
  bio: {
    type: String,
    default: ''
  },
  college: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'College',
    required: true
  },
  studentId: {
    type: String,
    trim: true
  },
  major: {
    type: String,
    trim: true
  },
  gradYear: {
    type: Number
  },
  role: {
    type: String,
    enum: ['student', 'faculty', 'admin', 'moderator'],
    default: 'student'
  },
  isVerified: {
    type: Boolean,
    default: false
  },
  verificationToken: {
    type: String
  },
  resetPasswordToken: {
    type: String
  },
  resetPasswordExpires: {
    type: Date
  },
  subscribedColleges: [{
    type: mongoose.Schema.Types.ObjectId,
    ref: 'College'
  }],
  subscribedCourses: [{
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Course'
  }],
  savedPosts: [{
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Post'
  }],
  upvotedPosts: [{
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Post'
  }],
  downvotedPosts: [{
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Post'
  }],
  upvotedComments: [{
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Comment'
  }],
  downvotedComments: [{
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Comment'
  }],
  karma: {
    type: Number,
    default: 0
  },
  lastActive: {
    type: Date,
    default: Date.now
  },
  createdAt: {
    type: Date,
    default: Date.now
  }
});

// Hash password before saving
UserSchema.pre('save', async function(next) {
  if (!this.isModified('password')) {
    return next();
  }
  
  try {
    const salt = await bcrypt.genSalt(10);
    this.password = await bcrypt.hash(this.password, salt);
    next();
  } catch (error) {
    next(error);
  }
});

// Compare passwords
UserSchema.methods.comparePassword = async function(candidatePassword) {
  try {
    return await bcrypt.compare(candidatePassword, this.password);
  } catch (error) {
    throw error;
  }
};

// Virtual for full name
UserSchema.virtual('fullName').get(function() {
  return `${this.firstName} ${this.lastName}`;
});

// Calculate karma
UserSchema.methods.calculateKarma = async function() {
  try {
    const Post = mongoose.model('Post');
    const Comment = mongoose.model('Comment');
    
    const posts = await Post.find({ author: this._id });
    const comments = await Comment.find({ author: this._id });
    
    let karma = 0;
    
    // Add post karma (upvotes - downvotes)
    posts.forEach(post => {
      karma += post.upvotes.length - post.downvotes.length;
    });
    
    // Add comment karma
    comments.forEach(comment => {
      karma += comment.upvotes.length - comment.downvotes.length;
    });
    
    this.karma = karma;
    await this.save();
    
    return karma;
  } catch (error) {
    throw error;
  }
};

module.exports = mongoose.model('User', UserSchema);