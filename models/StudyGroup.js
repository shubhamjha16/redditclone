const mongoose = require('mongoose');
const slugify = require('slugify');

const StudyGroupSchema = new mongoose.Schema({
  name: {
    type: String,
    required: [true, 'Study group name is required'],
    trim: true,
    maxlength: [100, 'Name cannot exceed 100 characters']
  },
  slug: {
    type: String,
    unique: true
  },
  description: {
    type: String,
    required: [true, 'Description is required']
  },
  college: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'College',
    required: true
  },
  course: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Course'
  },
  creator: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true
  },
  moderators: [{
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User'
  }],
  members: [{
    user: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'User'
    },
    role: {
      type: String,
      enum: ['member', 'moderator', 'leader'],
      default: 'member'
    },
    joinedAt: {
      type: Date,
      default: Date.now
    }
  }],
  memberCount: {
    type: Number,
    default: 0
  },
  memberLimit: {
    type: Number,
    default: 20
  },
  schedule: [{
    day: {
      type: String,
      enum: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    },
    startTime: String,
    endTime: String,
    location: {
      type: String
    },
    isVirtual: {
      type: Boolean,
      default: false
    },
    meetingLink: {
      type: String
    }
  }],
  topics: [{
    type: String,
    trim: true
  }],
  goals: [{
    description: {
      type: String,
      required: true
    },
    isCompleted: {
      type: Boolean,
      default: false
    }
  }],
  resources: [{
    title: {
      type: String,
      required: true
    },
    url: String,
    description: String,
    type: {
      type: String,
      enum: ['document', 'link', 'video', 'other'],
      default: 'other'
    },
    addedBy: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'User'
    },
    addedAt: {
      type: Date,
      default: Date.now
    }
  }],
  joinCode: {
    type: String,
    unique: true
  },
  status: {
    type: String,
    enum: ['active', 'completed', 'cancelled'],
    default: 'active'
  },
  privacy: {
    type: String,
    enum: ['public', 'private', 'invite-only'],
    default: 'public'
  },
  startDate: {
    type: Date
  },
  endDate: {
    type: Date
  },
  meetingFrequency: {
    type: String,
    enum: ['daily', 'weekly', 'bi-weekly', 'monthly', 'as-needed'],
    default: 'weekly'
  },
  tags: [{
    type: String,
    trim: true
  }],
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

// Create slug and generate join code before saving
StudyGroupSchema.pre('save', function(next) {
  if (this.isModified('name')) {
    const baseSlug = slugify(this.name, { lower: true, strict: true });
    // Add a random string to ensure uniqueness
    this.slug = `${baseSlug}-${(Math.random() * Math.pow(36, 4) | 0).toString(36)}`;
  }
  
  // Generate join code if new and privacy is invite-only or private
  if (this.isNew && !this.joinCode && (this.privacy === 'invite-only' || this.privacy === 'private')) {
    this.joinCode = Math.random().toString(36).substring(2, 8).toUpperCase();
  }
  
  // Update member count
  if (this.isModified('members')) {
    this.memberCount = this.members.length;
  }
  
  this.updatedAt = Date.now();
  next();
});

// Virtual for study group discussions (posts)
StudyGroupSchema.virtual('discussions', {
  ref: 'Post',
  localField: '_id',
  foreignField: 'studyGroup',
  justOne: false
});

// Virtual for study group upcoming sessions (events)
StudyGroupSchema.virtual('sessions', {
  ref: 'Event',
  localField: '_id',
  foreignField: 'studyGroup',
  justOne: false
});

// Method to add member
StudyGroupSchema.methods.addMember = async function(userId, role = 'member') {
  // Check if user is already a member
  const existingMember = this.members.find(member => 
    member.user.toString() === userId.toString()
  );
  
  if (existingMember) {
    return this; // User already a member
  }
  
  // Check if at member limit
  if (this.memberCount >= this.memberLimit) {
    throw new Error('Study group has reached its member limit');
  }
  
  // Add new member
  this.members.push({
    user: userId,
    role: role,
    joinedAt: Date.now()
  });
  
  this.memberCount = this.members.length;
  this.lastActiveAt = Date.now();
  
  return this.save();
};

// Method to remove member
StudyGroupSchema.methods.removeMember = async function(userId) {
  this.members = this.members.filter(member => 
    member.user.toString() !== userId.toString()
  );
  
  this.memberCount = this.members.length;
  
  return this.save();
};

// Method to update member role
StudyGroupSchema.methods.updateMemberRole = async function(userId, newRole) {
  const memberIndex = this.members.findIndex(member => 
    member.user.toString() === userId.toString()
  );
  
  if (memberIndex === -1) {
    throw new Error('User is not a member of this study group');
  }
  
  this.members[memberIndex].role = newRole;
  
  return this.save();
};

// Static method to get upcoming study sessions for a user
StudyGroupSchema.statics.getUpcomingSessions = async function(userId) {
  try {
    // First get all study groups where user is a member
    const studyGroups = await this.find({
      'members.user': userId,
      status: 'active'
    }).select('_id');
    
    const studyGroupIds = studyGroups.map(group => group._id);
    
    // Then get upcoming events related to these study groups
    const Event = mongoose.model('Event');
    const now = new Date();
    
    const upcomingSessions = await Event.find({
      studyGroup: { $in: studyGroupIds },
      startTime: { $gte: now }
    })
    .sort({ startTime: 1 })
    .populate('studyGroup', 'name slug')
    .populate('college', 'name slug')
    .populate('course', 'code name')
    .limit(10)
    .lean();
    
    return upcomingSessions;
  } catch (error) {
    throw error;
  }
};

// Static method to search study groups
StudyGroupSchema.statics.searchStudyGroups = async function(collegeId, query, options = {}) {
  const searchRegex = new RegExp(query, 'i');
  
  const queryObj = {
    college: collegeId,
    status: 'active',
    $or: [
      { name: searchRegex },
      { description: searchRegex },
      { topics: searchRegex },
      { tags: searchRegex }
    ]
  };
  
  // Add course filter if provided
  if (options.courseId) {
    queryObj.course = options.courseId;
  }
  
  // Add privacy filter for public groups if not searching for user's groups
  if (!options.includeUserGroups) {
    queryObj.privacy = 'public';
  }
  
  let query1 = this.find(queryObj);
  
  // Add user's private groups if requested
  if (options.includeUserGroups && options.userId) {
    const userGroups = await this.find({
      college: collegeId,
      'members.user': options.userId,
      status: 'active'
    });
    
    // Combine results
    const publicGroups = await query1.exec();
    return [...publicGroups, ...userGroups];
  }
  
  return query1
    .populate('creator', 'username profileImage')
    .populate('course', 'code name')
    .sort({ memberCount: -1, lastActiveAt: -1 })
    .limit(options.limit || 20)
    .lean();
};

module.exports = mongoose.model('StudyGroup', StudyGroupSchema);