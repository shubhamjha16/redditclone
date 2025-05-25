const mongoose = require('mongoose');
const slugify = require('slugify');

const CollegeSchema = new mongoose.Schema({
  name: {
    type: String,
    required: true,
    unique: true,
    trim: true
  },
  slug: {
    type: String,
    unique: true
  },
  description: {
    type: String,
    required: true
  },
  location: {
    city: {
      type: String,
      required: true
    },
    state: {
      type: String,
      required: true
    },
    country: {
      type: String,
      required: true
    }
  },
  website: {
    type: String,
    required: true
  },
  logo: {
    type: String,
    default: 'default-college-logo.png'
  },
  bannerImage: {
    type: String,
    default: 'default-college-banner.jpg'
  },
  colors: {
    primary: {
      type: String,
      default: '#0066cc'
    },
    secondary: {
      type: String,
      default: '#ffffff'
    }
  },
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
  verificationRequired: {
    type: Boolean,
    default: true
  },
  verificationDomain: {
    type: String
  },
  isPublic: {
    type: Boolean,
    default: true
  },
  isActive: {
    type: Boolean,
    default: true
  },
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

// Create college slug from name
CollegeSchema.pre('save', function(next) {
  if (this.isModified('name')) {
    this.slug = slugify(this.name, { lower: true });
  }
  
  if (this.isModified('subscribers')) {
    this.subscriberCount = this.subscribers.length;
  }
  
  this.updatedAt = Date.now();
  next();
});

// Virtual for college posts
CollegeSchema.virtual('posts', {
  ref: 'Post',
  localField: '_id',
  foreignField: 'college',
  justOne: false
});

// Virtual for college courses
CollegeSchema.virtual('courses', {
  ref: 'Course',
  localField: '_id',
  foreignField: 'college',
  justOne: false
});

// Virtual for college events
CollegeSchema.virtual('events', {
  ref: 'Event',
  localField: '_id',
  foreignField: 'college',
  justOne: false
});

// Virtual for college study groups
CollegeSchema.virtual('studyGroups', {
  ref: 'StudyGroup',
  localField: '_id',
  foreignField: 'college',
  justOne: false
});

// Format location
CollegeSchema.virtual('formattedLocation').get(function() {
  return `${this.location.city}, ${this.location.state}, ${this.location.country}`;
});

// Static method to get trending colleges
CollegeSchema.statics.getTrendingColleges = async function(limit = 5) {
  const Post = mongoose.model('Post');
  
  // Get colleges with most recent activity
  const collegeActivity = await Post.aggregate([
    { $match: { createdAt: { $gte: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000) } } }, // Last 7 days
    { $group: { _id: '$college', postCount: { $sum: 1 } } },
    { $sort: { postCount: -1 } },
    { $limit: limit }
  ]);
  
  const collegeIds = collegeActivity.map(item => item._id);
  
  return this.find({ _id: { $in: collegeIds } })
    .populate('moderators', 'username profileImage')
    .lean();
};

module.exports = mongoose.model('College', CollegeSchema);