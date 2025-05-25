const mongoose = require('mongoose');
const slugify = require('slugify');

const CourseSchema = new mongoose.Schema({
  college: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'College',
    required: true
  },
  code: {
    type: String,
    required: true,
    trim: true
  },
  name: {
    type: String,
    required: true,
    trim: true
  },
  slug: {
    type: String,
    unique: true
  },
  description: {
    type: String
  },
  department: {
    type: String,
    required: true,
    trim: true
  },
  credits: {
    type: Number
  },
  professors: [{
    name: {
      type: String,
      required: true
    },
    email: String,
    profileImage: String
  }],
  term: {
    type: String,
    enum: ['Fall', 'Spring', 'Summer', 'Winter', 'Year-Round'],
    default: 'Year-Round'
  },
  year: {
    type: Number
  },
  schedule: {
    days: [String],
    startTime: String,
    endTime: String,
    location: String
  },
  syllabus: {
    type: String
  },
  prerequisites: [String],
  topics: [String],
  subscribers: [{
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User'
  }],
  subscriberCount: {
    type: Number,
    default: 0
  },
  moderators: [{
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User'
  }],
  icon: {
    type: String,
    default: 'default-course-icon.png'
  },
  isActive: {
    type: Boolean,
    default: true
  },
  isVerified: {
    type: Boolean,
    default: false
  },
  verifiedBy: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User'
  },
  createdBy: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true
  },
  resourceLinks: [{
    title: {
      type: String,
      required: true
    },
    url: {
      type: String,
      required: true
    },
    type: {
      type: String,
      enum: ['textbook', 'video', 'website', 'document', 'other'],
      default: 'other'
    },
    description: String
  }],
  createdAt: {
    type: Date,
    default: Date.now
  },
  updatedAt: {
    type: Date,
    default: Date.now
  }
}, {
  toJSON: { virtuals: true },
  toObject: { virtuals: true }
});

// Create slug from course code and name
CourseSchema.pre('save', function(next) {
  if (this.isModified('code') || this.isModified('name')) {
    const collegeId = this.college.toString();
    this.slug = `${collegeId}-${slugify(`${this.code} ${this.name}`, {
      lower: true,
      strict: true
    })}`;
  }
  
  if (this.isModified('subscribers')) {
    this.subscriberCount = this.subscribers.length;
  }
  
  this.updatedAt = Date.now();
  next();
});

// Virtual for course posts
CourseSchema.virtual('posts', {
  ref: 'Post',
  localField: '_id',
  foreignField: 'course',
  justOne: false
});

// Virtual for study groups
CourseSchema.virtual('studyGroups', {
  ref: 'StudyGroup',
  localField: '_id',
  foreignField: 'course',
  justOne: false
});

// Virtual for course events
CourseSchema.virtual('events', {
  ref: 'Event',
  localField: '_id',
  foreignField: 'course',
  justOne: false
});

// Static method to get formatted course code with name
CourseSchema.virtual('formattedName').get(function() {
  return `${this.code}: ${this.name}`;
});

// Static method to get trending courses
CourseSchema.statics.getTrendingCourses = async function(collegeId, limit = 5) {
  const Post = mongoose.model('Post');
  
  // Get courses with most recent activity
  const courseActivity = await Post.aggregate([
    { 
      $match: { 
        course: { $exists: true, $ne: null },
        createdAt: { $gte: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000) }, // Last 30 days
        ...(collegeId ? { college: mongoose.Types.ObjectId(collegeId) } : {})
      }
    },
    { $group: { _id: '$course', postCount: { $sum: 1 } } },
    { $sort: { postCount: -1 } },
    { $limit: limit }
  ]);
  
  const courseIds = courseActivity.map(item => item._id);
  
  return this.find({ _id: { $in: courseIds } })
    .populate('college', 'name slug')
    .lean();
};

// Search courses by keyword
CourseSchema.statics.searchCourses = async function(collegeId, query) {
  // Create regex for case-insensitive search
  const searchRegex = new RegExp(query, 'i');
  
  return this.find({
    college: collegeId,
    $or: [
      { code: searchRegex },
      { name: searchRegex },
      { department: searchRegex },
      { 'professors.name': searchRegex },
      { topics: searchRegex }
    ]
  })
  .limit(20)
  .populate('college', 'name slug')
  .sort({ code: 1 })
  .lean();
};

module.exports = mongoose.model('Course', CourseSchema);