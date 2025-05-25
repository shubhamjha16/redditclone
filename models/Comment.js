const mongoose = require('mongoose');

const CommentSchema = new mongoose.Schema({
  content: {
    type: String,
    required: [true, 'Comment content is required'],
    trim: true
  },
  post: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Post',
    required: true
  },
  author: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true
  },
  parent: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Comment',
    default: null
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
  isEdited: {
    type: Boolean,
    default: false
  },
  editedAt: {
    type: Date
  },
  status: {
    type: String,
    enum: ['active', 'removed', 'deleted'],
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
  }
}, {
  toJSON: { virtuals: true },
  toObject: { virtuals: true }
});

// Update score when votes change
CommentSchema.pre('save', function(next) {
  if (this.isModified('upvotes') || this.isModified('downvotes')) {
    this.score = this.upvotes.length - this.downvotes.length;
  }
  
  if (this.isModified('content') && !this.isNew) {
    this.isEdited = true;
    this.editedAt = Date.now();
  }
  
  next();
});

// Virtual for replies (nested comments)
CommentSchema.virtual('replies', {
  ref: 'Comment',
  localField: '_id',
  foreignField: 'parent',
  justOne: false,
  options: { sort: { score: -1 } }
});

// Middleware to update post comment count when a comment is added or removed
CommentSchema.post('save', async function() {
  try {
    const Post = mongoose.model('Post');
    // Only count active comments
    if (this.status === 'active') {
      // Find the post and update its comment count
      await Post.findByIdAndUpdate(this.post, { 
        $inc: { commentCount: 1 },
        lastActiveAt: Date.now()
      });
    }
  } catch (err) {
    console.error('Error updating post comment count:', err);
  }
});

CommentSchema.post('findOneAndUpdate', async function(doc) {
  try {
    const Post = mongoose.model('Post');
    // If comment status changed to/from active, update post comment count
    if (doc._update && doc._update.$set && doc._update.$set.status) {
      const increment = doc._update.$set.status === 'active' ? 1 : -1;
      
      await Post.findByIdAndUpdate(doc.post, { 
        $inc: { commentCount: increment },
        lastActiveAt: Date.now()
      });
    }
  } catch (err) {
    console.error('Error updating post comment count:', err);
  }
});

// Method to upvote
CommentSchema.methods.upvote = async function(userId) {
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
CommentSchema.methods.downvote = async function(userId) {
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

// Static method to get comment tree
CommentSchema.statics.getCommentTree = async function(postId) {
  try {
    // First get all top-level comments (no parent)
    const topLevelComments = await this.find({ post: postId, parent: null, status: 'active' })
      .sort({ score: -1 })
      .populate('author', 'username profileImage')
      .lean();
      
    // Then get all replies for this post
    const replies = await this.find({ post: postId, parent: { $ne: null }, status: 'active' })
      .sort({ score: -1 })
      .populate('author', 'username profileImage')
      .lean();
      
    // Group replies by parent ID for easy lookup
    const replyMap = {};
    replies.forEach(reply => {
      const parentId = reply.parent.toString();
      if (!replyMap[parentId]) {
        replyMap[parentId] = [];
      }
      replyMap[parentId].push(reply);
    });
    
    // Function to recursively build comment tree
    const buildCommentTree = (comments) => {
      return comments.map(comment => {
        const commentId = comment._id.toString();
        comment.replies = replyMap[commentId] ? buildCommentTree(replyMap[commentId]) : [];
        return comment;
      });
    };
    
    return buildCommentTree(topLevelComments);
  } catch (error) {
    throw error;
  }
};

module.exports = mongoose.model('Comment', CommentSchema);