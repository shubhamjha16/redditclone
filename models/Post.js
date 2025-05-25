const mongoose = require('mongoose');
const slugify = require('slugify');

const PostSchema = new mongoose.Schema({
  title: {
    type: String,
    required: [true, 'Title is required'],
    trim: true,
    maxlength: [300, 'Title cannot be more than 300 characters']
  },
  slug: {
    type: String,
    unique: true
  },
  content: {
    type: String,
    required: [true, 'Content is required']
  },
  type: {
    type: String,
    enum: ['text', 'link', 'image', 'video', 'poll', 'announcement'],
    default: 'text'
  },
  url: {
    type: String
  },
  mediaFiles: [{
    type: String
  }],
  tags: [{
    type: String,
    trim: true
  }],
  college: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'College',
    required: true
  },
  course: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Course'
  },
  author: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true
  },
  upvotes: [{
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User'
  }],
  downvotes: [{
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User'
  }],
  score: {
    type: Number,
    default: 0
  },
  commentCount: {
    type: Number,
    default: 0
  },
  viewCount: {
    type: Number,
    default: 0
  },
  isPinned: {
    type: Boolean,
    default: false
  },
  isLocked: {
    type: Boolean,
    default: false
  },
  isSpoiler: {
    type: Boolean,
    default: false
  },
  isNSFW: {
    type: Boolean,
    default: false
  },
  isEvent: {
    type: Boolean,
    default: false
  },
  flair: {
    text: String,
    color: String,
    backgroundColor: String
  },
  status: {
    type: String,
    enum: ['active', 'removed', 'deleted', 'pending'],
    default: 'active'
  },
  removedReason: {
    type: String
  },
  removedBy: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User'
  },
  createdAt: {
    type: Date,
    default: Date.now
  },
  updatedAt: {
    type: Date,
    default: Date.now
  },
  lastActiveAt: {
    type: Date,
    default: Date.now
  }
}, {
  toJSON: { virtuals: true },
  toObject: { virtuals: true }
});

// Create slug from title before saving
PostSchema.pre('save', function(next) {
  if (this.isModified('title')) {
    // Create base slug
    const baseSlug = slugify(this.title, {
      lower: true,
      strict: true
    });
    
    // Add a random string to ensure uniqueness
    this.slug = `${baseSlug}-${(Math.random() * Math.pow(36, 6) | 0).toString(36)}`;
  }
  
  // Update score and timestamps
  if (this.isModified('upvotes') || this.isModified('downvotes')) {
    this.score = this.upvotes.length - this.downvotes.length;
  }
  
  if (this.isModified()) {
    this.updatedAt = Date.now();
  }
  
  next();
});

// Virtual for comments
PostSchema.virtual('comments', {
  ref: 'Comment',
  localField: '_id',
  foreignField: 'post',
  justOne: false,
  options: { sort: { createdAt: 1 } }
});

// Static method to get trending posts
PostSchema.statics.getTrending = async function(collegeId, limit = 10) {
  const oneWeekAgo = new Date();
  oneWeekAgo.setDate(oneWeekAgo.getDate() - 7);
  
  const query = { 
    createdAt: { $gte: oneWeekAgo },
    status: 'active'
  };
  
  if (collegeId) {
    query.college = collegeId;
  }
  
  return this.find(query)
    .sort({ score: -1, commentCount: -1, viewCount: -1 })
    .limit(limit)
    .populate('author', 'username profileImage')
    .populate('college', 'name slug')
    .lean();
};

// Static method to get new posts
PostSchema.statics.getNew = async function(collegeId, limit = 20) {
  const query = { status: 'active' };
  
  if (collegeId) {
    query.college = collegeId;
  }
  
  return this.find(query)
    .sort({ createdAt: -1 })
    .limit(limit)
    .populate('author', 'username profileImage')
    .populate('college', 'name slug')
    .lean();
};

// Method to increment view count
PostSchema.methods.incrementView = async function() {
  this.viewCount += 1;
  this.lastActiveAt = Date.now();
  return this.save();
};

// Method to upvote
PostSchema.methods.upvote = async function(userId) {
  // Remove from downvotes if exists
  if (this.downvotes.includes(userId)) {
    this.downvotes = this.downvotes.filter(id => id.toString() !== userId.toString());
  }
  
  // Add to upvotes if not already there
  if (!this.upvotes.includes(userId)) {
    this.upvotes.push(userId);
  } else {
    // Remove upvote if already upvoted (toggle behavior)
    this.upvotes = this.upvotes.filter(id => id.toString() !== userId.toString());
  }
  
  this.score = this.upvotes.length - this.downvotes.length;
  return this.save();
};

// Method to downvote
PostSchema.methods.downvote = async function(userId) {
  // Remove from upvotes if exists
  if (this.upvotes.includes(userId)) {
    this.upvotes = this.upvotes.filter(id => id.toString() !== userId.toString());
  }
  
  // Add to downvotes if not already there
  if (!this.downvotes.includes(userId)) {
    this.downvotes.push(userId);
  } else {
    // Remove downvote if already downvoted (toggle behavior)
    this.downvotes = this.downvotes.filter(id => id.toString() !== userId.toString());
  }
  
  this.score = this.upvotes.length - this.downvotes.length;
  return this.save();
};

module.exports = mongoose.model('Post', PostSchema);