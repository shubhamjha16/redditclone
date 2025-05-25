const express = require('express');
const router = express.Router();
const { check, validationResult } = require('express-validator');
const multer = require('multer');
const path = require('path');
const fs = require('fs');
const College = require('../models/College');
const User = require('../models/User');
const Post = require('../models/Post');
const Course = require('../models/Course');
const Event = require('../models/Event');
const { ensureAuthenticated, isAdmin, isCollegeModerator } = require('../middleware/auth');

// Configure multer for file uploads
const storage = multer.diskStorage({
  destination: function(req, file, cb) {
    const dir = 'public/uploads/colleges';
    if (!fs.existsSync(dir)){
      fs.mkdirSync(dir, { recursive: true });
    }
    cb(null, dir);
  },
  filename: function(req, file, cb) {
    cb(null, 'college-' + Date.now() + path.extname(file.originalname));
  }
});

const upload = multer({ 
  storage: storage,
  fileFilter: function(req, file, callback) {
    const ext = path.extname(file.originalname);
    if(ext !== '.png' && ext !== '.jpg' && ext !== '.jpeg' && ext !== '.gif') {
      return callback(new Error('Only images are allowed'));
    }
    callback(null, true);
  },
  limits: {
    fileSize: 1024 * 1024 * 5 // 5MB
  }
});

// @route   GET /colleges
// @desc    Get list of colleges
// @access  Public
router.get('/', async (req, res) => {
  try {
    const colleges = await College.find({ isActive: true })
      .select('name slug description location logo subscriberCount')
      .sort({ subscriberCount: -1 })
      .lean();
    
    res.render('colleges/index', { 
      title: 'College Communities',
      colleges 
    });
  } catch (err) {
    console.error(err);
    req.flash('error_msg', 'Error loading colleges');
    res.redirect('/');
  }
});

// @route   GET /colleges/trending
// @desc    Get trending colleges
// @access  Public
router.get('/trending', async (req, res) => {
  try {
    const trendingColleges = await College.getTrendingColleges(10);
    res.json(trendingColleges);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Server error' });
  }
});

// @route   GET /colleges/create
// @desc    Show college creation form
// @access  Admin only
router.get('/create', ensureAuthenticated, isAdmin, (req, res) => {
  res.render('colleges/create', { title: 'Create New College' });
});

// @route   POST /colleges
// @desc    Create a new college
// @access  Admin only
router.post('/', [
  ensureAuthenticated,
  isAdmin,
  upload.fields([
    { name: 'logo', maxCount: 1 },
    { name: 'bannerImage', maxCount: 1 }
  ]),
  [
    check('name', 'Name is required').notEmpty(),
    check('description', 'Description is required').notEmpty(),
    check('city', 'City is required').notEmpty(),
    check('state', 'State is required').notEmpty(),
    check('country', 'Country is required').notEmpty(),
    check('website', 'Website is required').notEmpty().isURL()
  ]
], async (req, res) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.render('colleges/create', {
      title: 'Create New College',
      errors: errors.array(),
      formData: req.body
    });
  }

  try {
    const newCollege = new College({
      name: req.body.name,
      description: req.body.description,
      location: {
        city: req.body.city,
        state: req.body.state,
        country: req.body.country
      },
      website: req.body.website,
      verificationRequired: req.body.verificationRequired === 'on',
      verificationDomain: req.body.verificationDomain,
      isPublic: req.body.isPublic === 'on',
      moderators: [req.user.id],
      colors: {
        primary: req.body.primaryColor || '#0066cc',
        secondary: req.body.secondaryColor || '#ffffff'
      }
    });

    if (req.files.logo) {
      newCollege.logo = `/uploads/colleges/${req.files.logo[0].filename}`;
    }
    
    if (req.files.bannerImage) {
      newCollege.bannerImage = `/uploads/colleges/${req.files.bannerImage[0].filename}`;
    }

    await newCollege.save();
    req.flash('success_msg', 'College created successfully');
    res.redirect(`/colleges/${newCollege.slug}`);
  } catch (err) {
    console.error(err);
    req.flash('error_msg', 'Error creating college');
    res.render('colleges/create', {
      title: 'Create New College',
      formData: req.body
    });
  }
});

// @route   GET /colleges/:slug
// @desc    View college page
// @access  Public
router.get('/:slug', async (req, res) => {
  try {
    const college = await College.findOne({ slug: req.params.slug, isActive: true })
      .populate('moderators', 'username profileImage')
      .lean();
      
    if (!college) {
      req.flash('error_msg', 'College not found');
      return res.redirect('/colleges');
    }
    
    // Get trending posts for this college
    const trendingPosts = await Post.getTrending(college._id, 5);
    
    // Get new posts
    const newPosts = await Post.getNew(college._id, 20);
    
    // Get upcoming events
    const upcomingEvents = await Event.getUpcomingEvents(college._id, 5);
    
    // Check if user is subscribed
    let isSubscribed = false;
    let isModerator = false;
    
    if (req.isAuthenticated()) {
      const user = await User.findById(req.user.id);
      isSubscribed = user.subscribedColleges.some(id => id.toString() === college._id.toString());
      isModerator = college.moderators.some(mod => mod._id.toString() === req.user.id);
    }
    
    res.render('colleges/view', {
      title: college.name,
      college,
      trendingPosts,
      newPosts,
      upcomingEvents,
      isSubscribed,
      isModerator
    });
  } catch (err) {
    console.error(err);
    req.flash('error_msg', 'Error loading college');
    res.redirect('/colleges');
  }
});

// @route   GET /colleges/:slug/courses
// @desc    View college courses
// @access  Public
router.get('/:slug/courses', async (req, res) => {
  try {
    const college = await College.findOne({ slug: req.params.slug, isActive: true }).lean();
    
    if (!college) {
      req.flash('error_msg', 'College not found');
      return res.redirect('/colleges');
    }
    
    // Get courses for this college
    const courses = await Course.find({ college: college._id })
      .sort({ department: 1, code: 1 })
      .lean();
      
    // Group courses by department
    const departments = {};
    courses.forEach(course => {
      if (!departments[course.department]) {
        departments[course.department] = [];
      }
      departments[course.department].push(course);
    });
    
    res.render('colleges/courses', {
      title: `${college.name} - Courses`,
      college,
      departments,
      courses
    });
  } catch (err) {
    console.error(err);
    req.flash('error_msg', 'Error loading courses');
    res.redirect(`/colleges/${req.params.slug}`);
  }
});

// @route   GET /colleges/:slug/events
// @desc    View college events
// @access  Public
router.get('/:slug/events', async (req, res) => {
  try {
    const college = await College.findOne({ slug: req.params.slug, isActive: true }).lean();
    
    if (!college) {
      req.flash('error_msg', 'College not found');
      return res.redirect('/colleges');
    }
    
    // Get upcoming events for this college
    const upcomingEvents = await Event.getUpcomingEvents(college._id, 20);
    
    // Get past events
    const pastEvents = await Event.find({
      college: college._id,
      endTime: { $lt: new Date() },
      status: { $in: ['completed', 'canceled'] }
    })
    .sort({ endTime: -1 })
    .limit(10)
    .populate('organizer', 'username profileImage')
    .lean();
    
    res.render('colleges/events', {
      title: `${college.name} - Events`,
      college,
      upcomingEvents,
      pastEvents
    });
  } catch (err) {
    console.error(err);
    req.flash('error_msg', 'Error loading events');
    res.redirect(`/colleges/${req.params.slug}`);
  }
});

// @route   GET /colleges/:slug/about
// @desc    View college about page
// @access  Public
router.get('/:slug/about', async (req, res) => {
  try {
    const college = await College.findOne({ slug: req.params.slug, isActive: true })
      .populate('moderators', 'username profileImage')
      .lean();
    
    if (!college) {
      req.flash('error_msg', 'College not found');
      return res.redirect('/colleges');
    }
    
    // Get subscriber count
    const subscriberCount = college.subscriberCount;
    
    // Get post count
    const postCount = await Post.countDocuments({ college: college._id });
    
    // Get course count
    const courseCount = await Course.countDocuments({ college: college._id });
    
    res.render('colleges/about', {
      title: `${college.name} - About`,
      college,
      stats: {
        subscriberCount,
        postCount,
        courseCount
      }
    });
  } catch (err) {
    console.error(err);
    req.flash('error_msg', 'Error loading college information');
    res.redirect(`/colleges/${req.params.slug}`);
  }
});

// @route   POST /colleges/:id/subscribe
// @desc    Subscribe to a college
// @access  Private
router.post('/:id/subscribe', ensureAuthenticated, async (req, res) => {
  try {
    const college = await College.findById(req.params.id);
    
    if (!college) {
      return res.status(404).json({ success: false, message: 'College not found' });
    }
    
    const user = await User.findById(req.user.id);
    
    // Check if already subscribed
    const isSubscribed = user.subscribedColleges.includes(college._id);
    
    if (isSubscribed) {
      // Unsubscribe
      user.subscribedColleges = user.subscribedColleges.filter(id => id.toString() !== college._id.toString());
      college.subscribers = college.subscribers.filter(id => id.toString() !== user._id.toString());
    } else {
      // Subscribe
      user.subscribedColleges.push(college._id);
      college.subscribers.push(user._id);
    }
    
    await user.save();
    await college.save();
    
    return res.json({ 
      success: true, 
      subscribed: !isSubscribed,
      subscriberCount: college.subscriberCount
    });
  } catch (err) {
    console.error(err);
    res.status(500).json({ success: false, message: 'Server error' });
  }
});

// @route   GET /colleges/:slug/edit
// @desc    Edit college form
// @access  Admin or Moderator
router.get('/:slug/edit', ensureAuthenticated, async (req, res) => {
  try {
    const college = await College.findOne({ slug: req.params.slug }).lean();
    
    if (!college) {
      req.flash('error_msg', 'College not found');
      return res.redirect('/colleges');
    }
    
    // Check if user is admin or moderator
    const isMod = college.moderators.some(mod => mod.toString() === req.user.id);
    if (!req.user.isAdmin && !isMod) {
      req.flash('error_msg', 'Not authorized');
      return res.redirect(`/colleges/${req.params.slug}`);
    }
    
    res.render('colleges/edit', {
      title: `Edit ${college.name}`,
      college
    });
  } catch (err) {
    console.error(err);
    req.flash('error_msg', 'Error loading college');
    res.redirect('/colleges');
  }
});

// @route   PUT /colleges/:id
// @desc    Update college
// @access  Admin or Moderator
router.put('/:id', [
  ensureAuthenticated,
  upload.fields([
    { name: 'logo', maxCount: 1 },
    { name: 'bannerImage', maxCount: 1 }
  ]),
  [
    check('name', 'Name is required').notEmpty(),
    check('description', 'Description is required').notEmpty(),
    check('city', 'City is required').notEmpty(),
    check('state', 'State is required').notEmpty(),
    check('country', 'Country is required').notEmpty(),
    check('website', 'Website is required').notEmpty().isURL()
  ]
], async (req, res) => {
  try {
    const college = await College.findById(req.params.id);
    
    if (!college) {
      req.flash('error_msg', 'College not found');
      return res.redirect('/colleges');
    }
    
    // Check if user is admin or moderator
    const isMod = college.moderators.some(mod => mod.toString() === req.user.id);
    if (!req.user.isAdmin && !isMod) {
      req.flash('error_msg', 'Not authorized');
      return res.redirect(`/colleges/${college.slug}`);
    }
    
    // Update college
    college.name = req.body.name;
    college.description = req.body.description;
    college.location.city = req.body.city;
    college.location.state = req.body.state;
    college.location.country = req.body.country;
    college.website = req.body.website;
    college.verificationRequired = req.body.verificationRequired === 'on';
    college.verificationDomain = req.body.verificationDomain;
    college.isPublic = req.body.isPublic === 'on';
    college.colors.primary = req.body.primaryColor || college.colors.primary;
    college.colors.secondary = req.body.secondaryColor || college.colors.secondary;
    
    if (req.files.logo) {
      // Delete old logo if it exists
      if (college.logo && college.logo !== 'default-college-logo.png') {
        const oldPath = path.join(__dirname, '../public', college.logo);
        if (fs.existsSync(oldPath)) {
          fs.unlinkSync(oldPath);
        }
      }
      college.logo = `/uploads/colleges/${req.files.logo[0].filename}`;
    }
    
    if (req.files.bannerImage) {
      // Delete old banner if it exists
      if (college.bannerImage && college.bannerImage !== 'default-college-banner.jpg') {
        const oldPath = path.join(__dirname, '../public', college.bannerImage);
        if (fs.existsSync(oldPath)) {
          fs.unlinkSync(oldPath);
        }
      }
      college.bannerImage = `/uploads/colleges/${req.files.bannerImage[0].filename}`;
    }
    
    await college.save();
    req.flash('success_msg', 'College updated successfully');
    res.redirect(`/colleges/${college.slug}`);
  } catch (err) {
    console.error(err);
    req.flash('error_msg', 'Error updating college');
    res.redirect(`/colleges/${req.params.id}/edit`);
  }
});

// @route   GET /colleges/:slug/moderators
// @desc    View and manage moderators
// @access  Admin or Moderator
router.get('/:slug/moderators', ensureAuthenticated, async (req, res) => {
  try {
    const college = await College.findOne({ slug: req.params.slug })
      .populate('moderators', 'username profileImage email')
      .lean();
    
    if (!college) {
      req.flash('error_msg', 'College not found');
      return res.redirect('/colleges');
    }
    
    // Check if user is admin or moderator
    const isMod = college.moderators.some(mod => mod._id.toString() === req.user.id);
    if (!req.user.isAdmin && !isMod) {
      req.flash('error_msg', 'Not authorized');
      return res.redirect(`/colleges/${req.params.slug}`);
    }
    
    res.render('colleges/moderators', {
      title: `${college.name} - Moderators`,
      college,
      isAdmin: req.user.isAdmin
    });
  } catch (err) {
    console.error(err);
    req.flash('error_msg', 'Error loading moderators');
    res.redirect(`/colleges/${req.params.slug}`);
  }
});

// @route   POST /colleges/:id/moderators
// @desc    Add a moderator
// @access  Admin or Moderator
router.post('/:id/moderators', ensureAuthenticated, async (req, res) => {
  try {
    const { username } = req.body;
    const college = await College.findById(req.params.id);
    
    if (!college) {
      return res.status(404).json({ success: false, message: 'College not found' });
    }
    
    // Check if user is admin or moderator
    const isMod = college.moderators.some(mod => mod.toString() === req.user.id);
    if (!req.user.isAdmin && !isMod) {
      return res.status(403).json({ success: false, message: 'Not authorized' });
    }
    
    // Find user by username
    const user = await User.findOne({ username });
    if (!user) {
      return res.status(404).json({ success: false, message: 'User not found' });
    }
    
    // Check if already a moderator
    if (college.moderators.includes(user._id)) {
      return res.status(400).json({ success: false, message: 'User is already a moderator' });
    }
    
    // Add user as moderator
    college.moderators.push(user._id);
    await college.save();
    
    return res.json({ 
      success: true, 
      message: 'Moderator added successfully',
      moderator: {
        _id: user._id,
        username: user.username,
        profileImage: user.profileImage
      }
    });
  } catch (err) {
    console.error(err);
    res.status(500).json({ success: false, message: 'Server error' });
  }
});

// @route   DELETE /colleges/:collegeId/moderators/:userId
// @desc    Remove a moderator
// @access  Admin or Moderator
router.delete('/:collegeId/moderators/:userId', ensureAuthenticated, async (req, res) => {
  try {
    const college = await College.findById(req.params.collegeId);
    
    if (!college) {
      return res.status(404).json({ success: false, message: 'College not found' });
    }
    
    // Check if user is admin or moderator (and not removing themselves if last mod)
    const isMod = college.moderators.some(mod => mod.toString() === req.user.id);
    const isSelfRemoval = req.user.id === req.params.userId;
    
    if (!req.user.isAdmin && (!isMod || (isSelfRemoval && college.moderators.length === 1))) {
      return res.status(403).json({ success: false, message: 'Not authorized' });
    }
    
    // Remove moderator
    college.moderators = college.moderators.filter(mod => mod.toString() !== req.params.userId);
    await college.save();
    
    return res.json({ success: true, message: 'Moderator removed successfully' });
  } catch (err) {
    console.error(err);
    res.status(500).json({ success: false, message: 'Server error' });
  }
});

// @route   GET /colleges/search
// @desc    Search colleges
// @access  Public
router.get('/search', async (req, res) => {
  try {
    const { q } = req.query;
    
    if (!q) {
      return res.redirect('/colleges');
    }
    
    const searchRegex = new RegExp(q, 'i');
    
    const colleges = await College.find({
      isActive: true,
      $or: [
        { name: searchRegex },
        { description: searchRegex },
        { 'location.city': searchRegex },
        { 'location.state': searchRegex }
      ]
    })
    .select('name slug description location logo subscriberCount')
    .lean();
    
    res.render('colleges/search', {
      title: `Search Results: ${q}`,
      colleges,
      searchQuery: q
    });
  } catch (err) {
    console.error(err);
    req.flash('error_msg', 'Error searching colleges');
    res.redirect('/colleges');
  }
});

module.exports = router;