import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para agregar token a las peticiones
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interceptor para manejar errores de autenticación
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Si el error es 401 y no hemos intentado refrescar el token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await axios.post(`${API_URL}/auth/refresh/`, {
            refresh: refreshToken,
          });

          const { access } = response.data;
          localStorage.setItem('access_token', access);
          api.defaults.headers.common['Authorization'] = `Bearer ${access}`;
          originalRequest.headers.Authorization = `Bearer ${access}`;

          return api(originalRequest);
        }
      } catch (refreshError) {
        // Si falla el refresh, limpiar y redirigir a login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        delete api.defaults.headers.common['Authorization'];
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default api;

// Students
export const getStudents = (page?: number, pageSize?: number, filters?: Record<string, any>) => {
  const params = new URLSearchParams();
  if (page) params.append('page', page.toString());
  if (pageSize) params.append('page_size', pageSize.toString());
  
  // Agregar filtros
  if (filters) {
    Object.keys(filters).forEach(key => {
      const value = filters[key];
      if (value !== undefined && value !== null && value !== '') {
        params.append(key, String(value));
      }
    });
  }
  
  const queryString = params.toString();
  return api.get(`/students/students/${queryString ? `?${queryString}` : ''}`);
};
export const getStudent = (id: string) => api.get(`/students/students/${id}/`);
export const createStudent = (student: any) => api.post('/students/students/', student);
export const updateStudent = (id: string, student: any) => api.patch(`/students/students/${id}/`, student);
export const getStudentProgress = (id: string) => api.get(`/students/students/${id}/progress/`);

// Enrollments
export const getEnrollment = (studentId: string) => api.get(`/students/enrollments/?student=${studentId}`);
export const generateContract = (enrollmentId: string) => 
  api.get(`/students/enrollments/${enrollmentId}/generate_contract/`, { responseType: 'blob' });

// Student Documents
export const getStudentDocuments = (studentId: string) => 
  api.get(`/students/documents/?student=${studentId}`);
export const uploadDocument = (studentId: string, documentType: string, file: File) => {
  const formData = new FormData();
  formData.append('student', studentId);
  formData.append('document_type', documentType);
  formData.append('file', file);
  return api.post('/students/documents/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
};
export const updateDocumentStatus = (id: string, status: string, notes?: string) =>
  api.patch(`/students/documents/${id}/`, { status, notes });

// Careers
export const getCareers = () => api.get('/academics/careers/');
export const getCareerPensum = (id: string) => api.get(`/academics/careers/${id}/pensum/`);

// Course Enrollments
export const getCourseEnrollments = (studentId?: string) => {
  const url = studentId 
    ? `/academics/enrollments/by_student/?student_id=${studentId}`
    : '/academics/enrollments/';
  return api.get(url);
};
export const createCourseEnrollment = (enrollment: any) => 
  api.post('/academics/enrollments/', enrollment);
export const updateCourseGrade = (id: string, grade: number) => 
  api.patch(`/academics/enrollments/${id}/update_grade/`, { final_grade: grade });
export const deleteCourseEnrollment = (id: string) =>
  api.delete(`/academics/enrollments/${id}/`);

// Courses
export const getCourses = (careerId?: string) => {
  const url = careerId 
    ? `/academics/courses/?career=${careerId}`
    : '/academics/courses/';
  return api.get(url);
};
export const getCourse = (id: string) => api.get(`/academics/courses/${id}/`);

// Payments
export const getPayments = (page?: number, pageSize?: number, filters?: Record<string, any>) => {
  const params = new URLSearchParams();
  if (page) params.append('page', page.toString());
  if (pageSize) params.append('page_size', pageSize.toString());
  
  // Agregar filtros
  if (filters) {
    Object.keys(filters).forEach(key => {
      const value = filters[key];
      if (value !== undefined && value !== null && value !== '') {
        params.append(key, String(value));
      }
    });
  }
  
  const queryString = params.toString();
  return api.get(`/payments/payments/${queryString ? `?${queryString}` : ''}`);
};
export const createPayment = (payment: any) => api.post('/payments/payments/', payment);
export const getStudentPaymentStatus = (studentId: string) => 
  api.get(`/payments/payments/student_status/?student_id=${studentId}`);
export const approvePayment = (id: string) => api.patch(`/payments/payments/${id}/approve/`, {});
export const rejectPayment = (id: string, notes?: string) => 
  api.patch(`/payments/payments/${id}/reject/`, { notes });
export const uploadPaymentReceipt = (paymentId: string, file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  return api.post(`/payments/payments/${paymentId}/upload_receipt/`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
};

// Scholarships
export const getScholarships = () => api.get('/payments/scholarships/');
export const createScholarship = (scholarship: any) => api.post('/payments/scholarships/', scholarship);

// Thesis
export const getThesis = (studentId: string) => 
  api.get(`/academics/thesis/by_student/?student_id=${studentId}`);
export const updateThesisStatus = (id: string, status: string) => 
  api.patch(`/academics/thesis/${id}/update_status/`, { status });

// Public Payment APIs (no authentication required)
export const getStudentByCarnet = (carnet: string) => 
  api.get(`/payments/public/student/?carnet=${carnet}`);
export const getPaymentTypes = () => api.get('/payments/payment-types/');
export const createPaymentIntent = (paymentData: any) => 
  api.post('/payments/public/payment-intent/', paymentData);
export const processPublicPayment = (paymentData: any) => 
  api.post('/payments/public/payment/', paymentData);

