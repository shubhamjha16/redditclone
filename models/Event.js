const mongoose = require('mongoose');
const slugify = require('slugify');

const EventSchema = new mongoose.Schema({
  title: {
    type: String,
    required: [true, 'Event title is required'],
    trim: true
  },
  slug: {
    type: String,
    unique: true
  },
  description: {
    type: String,
    required: [true, 'Event description is required']
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
  studyGroup: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'StudyGroup'
  },
  organizer: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true
  },
  startTime: {
    type: Date,
    required: [true, 'Start time is required']
  },
  endTime: {
    type: Date,
    required: [true, 'End time is required']
  },
  location: {
    name: {
      type: String,
      required: [true, 'Location name is required']
    },
    address: String,
    building: String,
    room: String,
    isVirtual: {
      type: Boolean,
      default: false
    },
    meetingLink: String,
    meetingId: String,
    meetingPassword: String
  },
  eventType: {
    type: String,
    enum: ['academic', 'social', 'career', 'study', 'club', 'sports', 'other'],
    default: 'other'
  },
  coverImage: {
    type: String,
    default: 'default-event-cover.jpg'
  },
  registrationRequired: {
    type: Boolean,
    default: false
  },
  registrationDeadline: {
    type: Date
  },
  maxAttendees: {
    type: Number
  },
  attendees: [{
    user: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'User'
    },
    status: {
      type: String,
      enum: ['registered', 'attended', 'canceled'],
      default: 'registered'
    },
    registeredAt: {
      type: Date,
      default: Date.now
    }
  }],
  attendeeCount: {
    type: Number,
    default: 0
  },
  interestedUsers: [{
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User'
  }],
  interestedCount: {
    type: Number,
    default: 0
  },
  tags: [{
    type: String,
    trim: true
  }],
  visibility: {
    type: String,
    enum: ['public', 'college-only', 'private'],
    default: 'college-only'
  },
  status: {
    type: String,
    enum: ['scheduled', 'canceled', 'completed', 'rescheduled'],
    default: 'scheduled'
  },
  recurrence: {
    isRecurring: {
      type: Boolean,
      default: false
    },
    pattern: {
      type: String,
      enum: ['daily', 'weekly', 'biweekly', 'monthly'],
    },
    endDate: Date,
    excludeDates: [Date]
  },
  relatedPost: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Post'
  },
  reminders: [{
    time: Date,
    sent: {
      type: Boolean,
      default: false
    }
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

// Create slug before saving
EventSchema.pre('save', function(next) {
  if (this.isModified('title')) {
    // Create base slug
    const baseSlug = slugify(this.title, {
      lower: true,
      strict: true
    });
    
    // Add date and random string to ensure uniqueness
    const dateStr = this.startTime ? 
      this.startTime.toISOString().split('T')[0] : 
      new Date().toISOString().split('T')[0];
      
    this.slug = `${baseSlug}-${dateStr}-${(Math.random() * Math.pow(36, 4) | 0).toString(36)}`;
  }
  
  // Update attendee count
  if (this.isModified('attendees')) {
    this.attendeeCount = this.attendees.length;
  }
  
  // Update interested count
  if (this.isModified('interestedUsers')) {
    this.interestedCount = this.interestedUsers.length;
  }
  
  this.updatedAt = Date.now();
  next();
});

// Check if event has ended
EventSchema.virtual('hasEnded').get(function() {
  return new Date() > this.endTime;
});

// Check if registration is open
EventSchema.virtual('isRegistrationOpen').get(function() {
  if (!this.registrationRequired) {
    return true;
  }
  
  const now = new Date();
  if (this.registrationDeadline && now > this.registrationDeadline) {
    return false;
  }
  
  if (this.maxAttendees && this.attendeeCount >= this.maxAttendees) {
    return false;
  }
  
  return true;
});

// Virtual for time until event
EventSchema.virtual('timeUntil').get(function() {
  const now = new Date();
  const diff = this.startTime - now;
  
  if (diff < 0) return 'Event has started';
  
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));
  const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
  
  if (days > 0) {
    return `${days} day${days > 1 ? 's' : ''} ${hours} hr${hours !== 1 ? 's' : ''}`;
  } else if (hours > 0) {
    return `${hours} hour${hours > 1 ? 's' : ''} ${minutes} min${minutes !== 1 ? 's' : ''}`;
  } else {
    return `${minutes} minute${minutes !== 1 ? 's' : ''}`;
  }
});

// Method to register user for event
EventSchema.methods.registerAttendee = async function(userId) {
  // Check if registration is open
  if (!this.isRegistrationOpen) {
    throw new Error('Registration is closed for this event');
  }
  
  // Check if user is already registered
  const isRegistered = this.attendees.some(attendee => 
    attendee.user.toString() === userId.toString() && 
    attendee.status !== 'canceled'
  );
  
  if (isRegistered) {
    throw new Error('User already registered for this event');
  }
  
  // Add user to attendees
  this.attendees.push({
    user: userId,
    status: 'registered',
    registeredAt: Date.now()
  });
  
  this.attendeeCount = this.attendees.filter(a => a.status !== 'canceled').length;
  
  return this.save();
};

// Method to cancel registration
EventSchema.methods.cancelRegistration = async function(userId) {
  const attendeeIndex = this.attendees.findIndex(attendee => 
    attendee.user.toString() === userId.toString() && 
    attendee.status === 'registered'
  );
  
  if (attendeeIndex === -1) {
    throw new Error('User is not registered for this event');
  }
  
  this.attendees[attendeeIndex].status = 'canceled';
  this.attendeeCount = this.attendees.filter(a => a.status !== 'canceled').length;
  
  return this.save();
};

// Method to mark user as interested
EventSchema.methods.toggleInterested = async function(userId) {
  const isInterested = this.interestedUsers.some(user => 
    user.toString() === userId.toString()
  );
  
  if (isInterested) {
    // Remove from interested
    this.interestedUsers = this.interestedUsers.filter(user => 
      user.toString() !== userId.toString()
    );
  } else {
    // Add to interested
    this.interestedUsers.push(userId);
  }
  
  this.interestedCount = this.interestedUsers.length;
  
  return this.save();
};

// Static method to get upcoming events for college
EventSchema.statics.getUpcomingEvents = async function(collegeId, limit = 10) {
  const now = new Date();
  
  return this.find({
    college: collegeId,
    startTime: { $gte: now },
    status: { $nin: ['canceled', 'completed'] },
    visibility: { $in: ['public', 'college-only'] }
  })
  .sort({ startTime: 1 })
  .limit(limit)
  .populate('organizer', 'username profileImage')
  .populate('course', 'code name')
  .populate('studyGroup', 'name')
  .lean();
};

// Static method to get events user is attending
EventSchema.statics.getUserEvents = async function(userId, options = {}) {
  const now = new Date();
  const query = { 'attendees.user': userId };
  
  if (options.upcoming) {
    query.startTime = { $gte: now };
    query.status = { $nin: ['canceled', 'completed'] };
  } else if (options.past) {
    query.$or = [
      { endTime: { $lt: now } },
      { status: 'completed' }
    ];
  }
  
  return this.find(query)
    .sort(options.upcoming ? { startTime: 1 } : { startTime: -1 })
    .limit(options.limit || 20)
    .populate('organizer', 'username profileImage')
    .populate('college', 'name slug')
    .populate('course', 'code name')
    .populate('studyGroup', 'name')
    .lean();
};

// Static method to search events
EventSchema.statics.searchEvents = async function(collegeId, query, options = {}) {
  const searchRegex = new RegExp(query, 'i');
  const now = new Date();
  
  const queryObj = {
    college: collegeId,
    $or: [
      { title: searchRegex },
      { description: searchRegex },
      { tags: searchRegex },
      { 'location.name': searchRegex },
      { 'location.building': searchRegex }
    ],
    visibility: { $in: ['public', 'college-only'] }
  };
  
  // Filter by date
  if (options.upcoming) {
    queryObj.startTime = { $gte: now };
    queryObj.status = { $nin: ['canceled', 'completed'] };
  } else if (options.past) {
    queryObj.$or = [
      { endTime: { $lt: now } },
      { status: 'completed' }
    ];
  }
  
  // Filter by type
  if (options.eventType) {
    queryObj.eventType = options.eventType;
  }
  
  return this.find(queryObj)
    .sort(options.upcoming ? { startTime: 1 } : { startTime: -1 })
    .limit(options.limit || 20)
    .populate('organizer', 'username profileImage')
    .populate('college', 'name slug')
    .populate('course', 'code name')
    .populate('studyGroup', 'name')
    .lean();
};

module.exports = mongoose.model('Event', EventSchema);