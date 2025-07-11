import React, { useState, useEffect, createContext, useContext } from 'react';
import './App.css';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = createContext();

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const savedUser = localStorage.getItem('user');
    if (savedUser) {
      setUser(JSON.parse(savedUser));
    }
    setIsLoading(false);
  }, []);

  const login = async (email, password) => {
    try {
      const response = await axios.post(`${API}/auth/login`, { email, password });
      const userData = response.data.user;
      setUser(userData);
      localStorage.setItem('user', JSON.stringify(userData));
      return { success: true };
    } catch (error) {
      return { success: false, error: error.response?.data?.detail || 'Login failed' };
    }
  };

  const register = async (email, password, name, role = 'user') => {
    try {
      const response = await axios.post(`${API}/auth/register`, { email, password, name, role });
      return { success: true };
    } catch (error) {
      return { success: false, error: error.response?.data?.detail || 'Registration failed' };
    }
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('user');
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
};

const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Login Modal Component
const LoginModal = ({ isOpen, onClose, onSuccess }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: '',
    role: 'user'
  });
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login, register } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    let result;
    if (isLogin) {
      result = await login(formData.email, formData.password);
    } else {
      result = await register(formData.email, formData.password, formData.name, formData.role);
    }

    if (result.success) {
      if (isLogin) {
        onSuccess();
      } else {
        setIsLogin(true);
        setError('Registration successful! Please login.');
      }
    } else {
      setError(result.error);
    }
    setIsLoading(false);
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white p-8 rounded-lg shadow-xl max-w-md w-full mx-4">
        <h2 className="text-2xl font-bold mb-6 text-center text-gray-800">
          {isLogin ? 'Login' : 'Register'}
        </h2>
        
        {error && (
          <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {!isLogin && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Name
              </label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Email
            </label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Password
            </label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>



          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {isLoading ? 'Loading...' : (isLogin ? 'Login' : 'Register')}
          </button>
        </form>

        <div className="mt-4 text-center">
          <button
            onClick={() => {
              setIsLogin(!isLogin);
              setError('');
            }}
            className="text-blue-600 hover:text-blue-800 text-sm"
          >
            {isLogin ? "Don't have an account? Register" : "Already have an account? Login"}
          </button>
        </div>

        <button
          onClick={onClose}
          className="absolute top-2 right-2 text-gray-400 hover:text-gray-600"
        >
          ×
        </button>
      </div>
    </div>
  );
};

// Student Modal Component
const StudentModal = ({ student, isOpen, onClose, onUpdate }) => {
  const [activeTab, setActiveTab] = useState('details');
  const [subjects, setSubjects] = useState([]);
  const [currentSemester, setCurrentSemester] = useState('1');
  const [isLoading, setIsLoading] = useState(false);
  const { user } = useAuth();

  const commonSubjects = [
    'Financial Management', 'Marketing Management', 'Human Resource Management', 
    'Operations Management', 'Strategic Management', 'Business Analytics',
    'Corporate Finance', 'Investment Management', 'Business Law', 'Economics',
    'Organizational Behavior', 'Project Management'
  ];

  useEffect(() => {
    if (student) {
      setCurrentSemester(student.current_semester || '1');
      const currentResults = student.semester_results?.find(sr => sr.semester === (student.current_semester || '1'));
      if (currentResults) {
        setSubjects(currentResults.subjects || []);
      } else {
        setSubjects(commonSubjects.slice(0, 6).map(name => ({ name, marks: 0, grade: 'F' })));
      }
    }
  }, [student]);

  const handleMarksChange = (index, marks) => {
    const newSubjects = [...subjects];
    newSubjects[index].marks = parseInt(marks) || 0;
    newSubjects[index].grade = calculateGrade(newSubjects[index].marks);
    setSubjects(newSubjects);
  };

  const calculateGrade = (marks) => {
    if (marks >= 90) return 'A+';
    if (marks >= 80) return 'A';
    if (marks >= 70) return 'B+';
    if (marks >= 60) return 'B';
    if (marks >= 50) return 'C';
    if (marks >= 40) return 'D';
    return 'F';
  };

  const handleSaveMarks = async () => {
    setIsLoading(true);
    try {
      await axios.put(`${API}/students/${student.id}/subjects?user_email=${user.email}`, {
        semester: currentSemester,
        subjects: subjects
      });
      onUpdate();
      alert('Marks updated successfully!');
    } catch (error) {
      console.error('Error updating marks:', error);
      alert('Failed to update marks');
    }
    setIsLoading(false);
  };

  if (!isOpen || !student) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white p-6 rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-gray-800">Student Details</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl"
          >
            ×
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="flex space-x-4 mb-6 border-b">
          <button
            onClick={() => setActiveTab('details')}
            className={`pb-2 px-4 font-medium ${
              activeTab === 'details'
                ? 'border-b-2 border-blue-500 text-blue-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Details
          </button>
          <button
            onClick={() => setActiveTab('marks')}
            className={`pb-2 px-4 font-medium ${
              activeTab === 'marks'
                ? 'border-b-2 border-blue-500 text-blue-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Marks & Grades
          </button>
        </div>

        {activeTab === 'details' && (
          <div className="space-y-4">
            <div className="flex items-center space-x-6">
              <div className="w-24 h-24 rounded-full overflow-hidden bg-gray-200 flex items-center justify-center">
                {student.photo ? (
                  <img
                    src={student.photo}
                    alt={student.name}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="text-gray-400 text-2xl">👤</div>
                )}
              </div>
              <div>
                <h3 className="text-xl font-semibold text-gray-800">{student.name}</h3>
                <p className="text-gray-600">Roll No: {student.roll_number}</p>
                <p className="text-gray-600">Stream: {student.stream}</p>
                <p className="text-gray-600">Current Semester: {student.current_semester}</p>
              </div>
            </div>

            {/* Semester History */}
            <div className="mt-6">
              <h4 className="text-lg font-semibold mb-3">Semester History</h4>
              <div className="space-y-2">
                {student.semester_results?.map((result, index) => (
                  <div key={index} className="p-3 bg-gray-50 rounded-lg">
                    <div className="flex justify-between items-center">
                      <span className="font-medium">Semester {result.semester}</span>
                      <span className="text-sm text-gray-500">
                        {result.subjects?.length || 0} subjects
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'marks' && (
          <div className="space-y-4">
            <div className="flex items-center space-x-4 mb-4">
              <label className="font-medium text-gray-700">Semester:</label>
              <select
                value={currentSemester}
                onChange={(e) => setCurrentSemester(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {[1, 2, 3, 4, 5, 6, 7, 8].map(sem => (
                  <option key={sem} value={sem.toString()}>{sem}</option>
                ))}
              </select>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full border-collapse border border-gray-300">
                <thead>
                  <tr className="bg-gray-50">
                    <th className="border border-gray-300 px-4 py-2 text-left">Subject</th>
                    <th className="border border-gray-300 px-4 py-2 text-left">Marks</th>
                    <th className="border border-gray-300 px-4 py-2 text-left">Grade</th>
                  </tr>
                </thead>
                <tbody>
                  {subjects.map((subject, index) => (
                    <tr key={index}>
                      <td className="border border-gray-300 px-4 py-2">{subject.name}</td>
                      <td className="border border-gray-300 px-4 py-2">
                        <input
                          type="number"
                          min="0"
                          max="100"
                          value={subject.marks}
                          onChange={(e) => handleMarksChange(index, e.target.value)}
                          className="w-20 px-2 py-1 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </td>
                      <td className="border border-gray-300 px-4 py-2">
                        <span className={`px-2 py-1 rounded text-sm font-medium ${
                          subject.grade === 'A+' || subject.grade === 'A' ? 'bg-green-100 text-green-800' :
                          subject.grade === 'B+' || subject.grade === 'B' ? 'bg-blue-100 text-blue-800' :
                          subject.grade === 'C' || subject.grade === 'D' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {subject.grade}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={handleSaveMarks}
                disabled={isLoading}
                className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
              >
                {isLoading ? 'Saving...' : 'Save Marks'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Student Card Component
const StudentCard = ({ student, onEdit, onDelete, isAdmin }) => {
  const [showModal, setShowModal] = useState(false);
  const [students, setStudents] = useState([]);

  const fetchStudents = async () => {
    // This will be called from parent component
  };

  return (
    <>
      <div className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition-shadow">
        <div className="flex items-center space-x-4 mb-4">
          <div className="w-16 h-16 rounded-full overflow-hidden bg-gray-200 flex items-center justify-center">
            {student.photo ? (
              <img
                src={student.photo}
                alt={student.name}
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="text-gray-400 text-xl">👤</div>
            )}
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-800">{student.name}</h3>
            <p className="text-gray-600 text-sm">Roll: {student.roll_number}</p>
            <p className="text-gray-600 text-sm">Stream: {student.stream}</p>
          </div>
        </div>

        <div className="flex justify-between items-center">
          <button
            onClick={() => setShowModal(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm"
          >
            View Details
          </button>
          {isAdmin && (
            <button
              onClick={() => onDelete(student.id)}
              className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors text-sm"
            >
              Delete
            </button>
          )}
        </div>
      </div>

      <StudentModal
        student={student}
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        onUpdate={fetchStudents}
      />
    </>
  );
};

// Main App Component
const App = () => {
  const [students, setStudents] = useState([]);
  const [users, setUsers] = useState([]);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [showAddStudentModal, setShowAddStudentModal] = useState(false);
  const [showUserManagementModal, setShowUserManagementModal] = useState(false);
  const [showAdminSettingsModal, setShowAdminSettingsModal] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const { user, logout, isLoading: authLoading } = useAuth();

  const fetchStudents = async () => {
    if (!user) return;
    
    setIsLoading(true);
    try {
      const response = await axios.get(`${API}/students?user_email=${user.email}`);
      setStudents(response.data);
    } catch (error) {
      console.error('Error fetching students:', error);
    }
    setIsLoading(false);
  };

  const fetchUsers = async () => {
    if (!user || user.role !== 'admin') return;
    
    try {
      const response = await axios.get(`${API}/users?user_email=${user.email}`);
      setUsers(response.data);
    } catch (error) {
      console.error('Error fetching users:', error);
    }
  };

  useEffect(() => {
    if (user) {
      fetchStudents();
      if (user.role === 'admin') {
        fetchUsers();
      }
    }
  }, [user]);

  const handleDeleteStudent = async (studentId) => {
    if (!window.confirm('Are you sure you want to delete this student?')) return;
    
    try {
      await axios.delete(`${API}/students/${studentId}?user_email=${user.email}`);
      fetchStudents();
    } catch (error) {
      console.error('Error deleting student:', error);
      alert('Failed to delete student');
    }
  };

  const handleAddStudent = async (studentData) => {
    try {
      await axios.post(`${API}/students?user_email=${user.email}`, studentData);
      fetchStudents();
      setShowAddStudentModal(false);
    } catch (error) {
      console.error('Error adding student:', error);
      alert('Failed to add student');
    }
  };

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-xl">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Navigation */}
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <a 
                href="https://gcet.edu.in/" 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-xl font-bold text-blue-600 hover:text-blue-800"
              >
                Geethanjali College of Engineering & Technology
              </a>
            </div>
            <div className="flex items-center space-x-4">
              {user ? (
                <>
                  <span className="text-gray-700">Welcome, {user.name}</span>
                  <span className="text-sm text-gray-500">({user.role})</span>
                  {user.role === 'admin' && (
                    <>
                      <button
                        onClick={() => setShowUserManagementModal(true)}
                        className="px-3 py-1 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors text-sm"
                      >
                        Manage Users
                      </button>
                      <button
                        onClick={() => setShowAdminSettingsModal(true)}
                        className="px-3 py-1 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors text-sm"
                      >
                        Settings
                      </button>
                    </>
                  )}
                  <button
                    onClick={logout}
                    className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
                  >
                    Logout
                  </button>
                </>
              ) : (
                <button
                  onClick={() => setShowLoginModal(true)}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                >
                  Login
                </button>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {user ? (
          <>
            {/* Header */}
            <div className="flex justify-between items-center mb-8">
              <h1 className="text-3xl font-bold text-gray-900">
                Student Management System
              </h1>
              <button
                onClick={() => setShowAddStudentModal(true)}
                className="px-6 py-3 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
              >
                Add Student
              </button>
            </div>

            {/* Students Grid */}
            {isLoading ? (
              <div className="text-center py-12">
                <div className="text-xl">Loading students...</div>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {students.map((student) => (
                  <StudentCard
                    key={student.id}
                    student={student}
                    onEdit={() => {}}
                    onDelete={handleDeleteStudent}
                    isAdmin={user.role === 'admin'}
                  />
                ))}
              </div>
            )}

            {students.length === 0 && !isLoading && (
              <div className="text-center py-12">
                <div className="text-xl text-gray-500">No students found</div>
                <p className="text-gray-400 mt-2">Add some students to get started!</p>
              </div>
            )}
          </>
        ) : (
          <div className="text-center py-12">
            <h1 className="text-3xl font-bold text-gray-900 mb-4">
              Welcome to Student Management System
            </h1>
            <p className="text-gray-600 mb-8">
              Please login to access the student management features
            </p>
            <button
              onClick={() => setShowLoginModal(true)}
              className="px-8 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-lg"
            >
              Login to Continue
            </button>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-gray-800 text-white py-4 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <p>Made with 💙 by <span className="font-semibold">ROHAN</span> (IIC Club)</p>
        </div>
      </footer>

      {/* Modals */}
      <LoginModal
        isOpen={showLoginModal}
        onClose={() => setShowLoginModal(false)}
        onSuccess={() => setShowLoginModal(false)}
      />

      <AddStudentModal
        isOpen={showAddStudentModal}
        onClose={() => setShowAddStudentModal(false)}
        onAdd={handleAddStudent}
      />
    </div>
  );
};

// Add Student Modal Component
const AddStudentModal = ({ isOpen, onClose, onAdd }) => {
  const [formData, setFormData] = useState({
    name: '',
    roll_number: '',
    stream: '',
    photo: '',
    current_semester: '1'
  });
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    await onAdd(formData);
    setIsLoading(false);
    setFormData({
      name: '',
      roll_number: '',
      stream: '',
      photo: '',
      current_semester: '1'
    });
  };

  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        setFormData({
          ...formData,
          photo: e.target.result
        });
      };
      reader.readAsDataURL(file);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white p-8 rounded-lg shadow-xl max-w-md w-full mx-4">
        <h2 className="text-2xl font-bold mb-6 text-center text-gray-800">
          Add New Student
        </h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Name
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({...formData, name: e.target.value})}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Roll Number
            </label>
            <input
              type="text"
              value={formData.roll_number}
              onChange={(e) => setFormData({...formData, roll_number: e.target.value})}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Stream
            </label>
            <select
              value={formData.stream}
              onChange={(e) => setFormData({...formData, stream: e.target.value})}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select Stream</option>
              <option value="MBA in Finance">MBA in Finance</option>
              <option value="MBA in Human Resources">MBA in Human Resources</option>
              <option value="MBA in Business Management">MBA in Business Management</option>
              <option value="MBA in Marketing">MBA in Marketing</option>
              <option value="MBA in Operations">MBA in Operations</option>
              <option value="MBA in Information Technology">MBA in Information Technology</option>
              <option value="MBA in International Business">MBA in International Business</option>
              <option value="MBA in Entrepreneurship">MBA in Entrepreneurship</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Current Semester
            </label>
            <select
              value={formData.current_semester}
              onChange={(e) => setFormData({...formData, current_semester: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {[1, 2, 3, 4, 5, 6, 7, 8].map(sem => (
                <option key={sem} value={sem.toString()}>{sem}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Photo
            </label>
            <input
              type="file"
              accept="image/*"
              onChange={handleImageUpload}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="flex space-x-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              {isLoading ? 'Adding...' : 'Add Student'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Wrap App with AuthProvider
const AppWithAuth = () => {
  return (
    <AuthProvider>
      <App />
    </AuthProvider>
  );
};

export default AppWithAuth;