import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// Crear instancia de axios
const api = axios.create({
  baseURL: API_BASE_URL,
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

// Interceptor para manejar respuestas y refresh token
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Si el error es 401 y no hemos intentado refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}/auth/refresh/`, {
            refresh: refreshToken,
          });

          const { access } = response.data;
          localStorage.setItem('access_token', access);

          // Reintentar la petición original con el nuevo token
          originalRequest.headers.Authorization = `Bearer ${access}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        // Si el refresh falla, hacer logout
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default api;

// Funciones de API específicas
export const authApi = {
  login: (username: string, password: string) =>
    api.post('/auth/login/', { username, password }),
  register: (data: any) => api.post('/users/register/', data),
  refreshToken: (refresh: string) => api.post('/auth/refresh/', { refresh }),
  getProfile: () => api.get('/users/profile/'),
  changePassword: (oldPassword: string, newPassword: string) =>
    api.post('/users/change_password/', { old_password: oldPassword, new_password: newPassword }),
};

export const studentsApi = {
  list: (params?: any) => api.get('/students/students/', { params }),
  get: (id: string | number) => api.get(`/students/students/${id}/`),
  create: (data: any) => api.post('/students/students/', data),
  update: (id: string | number, data: any) => api.patch(`/students/students/${id}/`, data),
  delete: (id: string | number) => api.delete(`/students/students/${id}/`),
  getProgress: (id: string | number) => api.get(`/students/students/${id}/progress/`),
};

export const documentsApi = {
  list: (params?: any) => api.get('/students/documents/', { params }),
  get: (id: string) => api.get(`/students/documents/${id}/`),
  getByStudent: (studentId: string | number) => api.get('/students/documents/', { params: { student: studentId } }),
  create: (data: any) => api.post('/students/documents/', data),
  update: (id: string, data: any) => api.patch(`/students/documents/${id}/`, data),
  delete: (id: string) => api.delete(`/students/documents/${id}/`),
  uploadFile: (id: string, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/students/documents/${id}/upload_file/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  updateStatus: (id: string, status: string, notes?: string) => 
    api.patch(`/students/documents/${id}/update_status/`, { status, notes }),
};

export const paymentsApi = {
  list: (params?: any) => api.get('/payments/payments/', { params }),
  get: (id: number) => api.get(`/payments/payments/${id}/`),
  create: (data: any) => api.post('/payments/payments/', data),
  approve: (id: string | number) => api.patch(`/payments/payments/${id}/approve/`),
  reject: (id: string | number, notes?: string) => api.patch(`/payments/payments/${id}/reject/`, notes ? { notes } : {}),
  uploadReceipt: (id: string | number, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/payments/payments/${id}/upload_receipt/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  updateReference: (id: string | number, reference: string) => 
    api.patch(`/payments/payments/${id}/update_reference/`, { payment_reference: reference }),
  getStudentStatus: (studentId: number) =>
    api.get(`/payments/payments/student_status/?student_id=${studentId}`),
  getPendingCount: () => api.get('/payments/payments/pending_count/'),
  getPendingTransfers: (params?: any) => api.get('/payments/payments/pending_transfers/', { params }),
  getStatistics: () => api.get('/payments/payments/statistics/'),
  createPaymentIntent: (data: any) => api.post('/payments/public/payment-intent/', data),
  processPublicPayment: (data: any) => api.post('/payments/public/payment/', data),
};

export const scholarshipsApi = {
  list: (params?: any) => api.get('/payments/scholarships/', { params }),
  get: (id: number) => api.get(`/payments/scholarships/${id}/`),
  create: (data: any) => api.post('/payments/scholarships/', data),
  update: (id: number, data: any) => api.patch(`/payments/scholarships/${id}/`, data),
  delete: (id: number) => api.delete(`/payments/scholarships/${id}/`),
};

export const paymentTypesApi = {
  list: (params?: any) => api.get('/payments/payment-types/', { params }),
  get: (id: number) => api.get(`/payments/payment-types/${id}/`),
};

export const academicsApi = {
  getCareers: () => api.get('/academics/careers/'),
  getCareer: (id: number) => api.get(`/academics/careers/${id}/`),
  getPensum: (id: number) => api.get(`/academics/careers/${id}/pensum/`),
  getEnrollments: (params?: any) => api.get('/academics/enrollments/', { params }),
  updateGrade: (id: string | number, grade: number) =>
    api.patch(`/academics/enrollments/${id}/update_grade/`, { final_grade: grade }),
  getCourses: (params?: any) => api.get('/academics/courses/', { params }),
  getCourse: (id: number) => api.get(`/academics/courses/${id}/`),
  createCourse: (data: any) => api.post('/academics/courses/', data),
  updateCourse: (id: number, data: any) => api.patch(`/academics/courses/${id}/`, data),
  deleteCourse: (id: number) => api.delete(`/academics/courses/${id}/`),
  createCourseEnrollment: (data: any) => api.post('/academics/enrollments/', data),
  getCuatrimestres: (params?: any) => api.get('/academics/cuatrimestres/', { params }),
  getThesis: (params?: any) => api.get('/academics/thesis/', { params }),
  getThesisByStudent: (studentId: string | number) => api.get('/academics/thesis/by_student/', { params: { student_id: studentId } }),
  updateThesisStatus: (id: string | number, status: string) => api.patch(`/academics/thesis/${id}/update_status/`, { status }),
  // Cuatrimestre Enrollments
  getCuatrimestreEnrollments: (params?: any) => api.get('/academics/cuatrimestre-enrollments/', { params }),
  getCuatrimestreEnrollment: (id: string | number) => api.get(`/academics/cuatrimestre-enrollments/${id}/`),
  createCuatrimestreEnrollment: (data: any) => api.post('/academics/cuatrimestre-enrollments/', data),
  updateCuatrimestreEnrollment: (id: string | number, data: any) => api.patch(`/academics/cuatrimestre-enrollments/${id}/`, data),
  deleteCuatrimestreEnrollment: (id: string | number) => api.delete(`/academics/cuatrimestre-enrollments/${id}/`),
  enrollCoursesInCuatrimestre: (id: string | number, courseIds: string[]) => 
    api.post(`/academics/cuatrimestre-enrollments/${id}/enroll_courses/`, { course_ids: courseIds }),
  preAssignCourses: (id: string | number, courseIds: string[]) => 
    api.post(`/academics/cuatrimestre-enrollments/${id}/pre_assign_courses/`, { course_ids: courseIds }),
  getCoursesInCuatrimestre: (id: string | number) => api.get(`/academics/cuatrimestre-enrollments/${id}/courses/`),
  getAvailableCourses: (id: string | number) => api.get(`/academics/cuatrimestre-enrollments/${id}/available_courses/`),
  previewBoleta: (id: string | number) => 
    api.get(`/academics/cuatrimestre-enrollments/${id}/preview_boleta/`, { responseType: 'blob' }),
  confirmCourseAssignment: (id: string | number) => 
    api.post(`/academics/cuatrimestre-enrollments/${id}/confirm_course_assignment/`),
  // Payment and enrollment flow
  processEnrollmentPayment: (id: string | number, data: { payment_method: string; payment_reference?: string; transfer_receipt?: File }) => {
    const formData = new FormData();
    formData.append('payment_method', data.payment_method);
    if (data.payment_reference) formData.append('payment_reference', data.payment_reference);
    if (data.transfer_receipt) formData.append('transfer_receipt', data.transfer_receipt);
    return api.post(`/academics/cuatrimestre-enrollments/${id}/process_enrollment_payment/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  approveEnrollmentPayment: (id: string | number) => 
    api.post(`/academics/cuatrimestre-enrollments/${id}/approve_enrollment_payment/`),
  rejectEnrollmentPayment: (id: string | number) => 
    api.post(`/academics/cuatrimestre-enrollments/${id}/reject_enrollment_payment/`),
  calculateTuition: (id: string | number) => 
    api.get(`/academics/cuatrimestre-enrollments/${id}/calculate_tuition/`),
  confirmAssignment: (id: string | number, paymentOption: 'monthly' | 'full') => 
    api.post(`/academics/cuatrimestre-enrollments/${id}/confirm_assignment/`, { payment_option: paymentOption }),
  getAssignmentSheet: (id: string | number) => 
    api.get(`/academics/cuatrimestre-enrollments/${id}/assignment_sheet/`),
  // Bulk grade upload
  bulkUploadGrades: (grades: Array<{ student_id: string; course_id: string; final_grade: number }>) =>
    api.post('/academics/enrollments/bulk_upload_grades/', { grades }),
  getEnrollmentsByCuatrimestre: (params: { cuatrimestre_enrollment_id?: string; academic_year?: number; cuatrimestre_id?: string }) =>
    api.get('/academics/enrollments/by_cuatrimestre/', { params }),
};

// Catálogos SEP
export const catalogosApi = {
  getPaises: (params?: any) => api.get('/students/catalogos/paises/', { params }),
  getEntidadesFederativas: (params?: any) => api.get('/students/catalogos/entidades-federativas/', { params }),
  getIdiomas: (params?: any) => api.get('/students/catalogos/idiomas/', { params }),
  getNecesidadesEducativas: (params?: any) => api.get('/students/catalogos/necesidades-educativas-especiales/', { params }),
  getAntecedentesAcademicos: (params?: any) => api.get('/students/catalogos/antecedentes-academicos/', { params }),
  getNivelesEducativos: (params?: any) => api.get('/students/catalogos/niveles-educativos/', { params }),
  getModalidadesEducativas: (params?: any) => api.get('/students/catalogos/modalidades-educativas/', { params }),
  getTurnos: (params?: any) => api.get('/students/catalogos/turnos/', { params }),
};

// Inscripciones (Enrollments)
export const enrollmentsApi = {
  list: (params?: any) => api.get('/students/enrollments/', { params }),
  get: (id: string) => api.get(`/students/enrollments/${id}/`),
  create: (data: any) => api.post('/students/enrollments/', data),
  update: (id: string, data: any) => api.patch(`/students/enrollments/${id}/`, data),
  delete: (id: string) => api.delete(`/students/enrollments/${id}/`),
  generateContract: (id: string) => api.get(`/students/enrollments/${id}/generate_contract/`, { responseType: 'blob' }),
  uploadScannedContract: (id: string, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post(`/students/enrollments/${id}/upload_scanned_contract/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  approveEnrollment: (id: string) => api.post(`/students/enrollments/${id}/approve_enrollment/`),
  rejectEnrollment: (id: string, reason?: string) => 
    api.post(`/students/enrollments/${id}/reject_enrollment/`, { reason }),
};

// Funciones auxiliares para compatibilidad con código existente
export function getStudents(paramsOrPage?: any, itemsPerPage?: number, filterParams?: any) {
  // Compatibilidad: si se pasa page, itemsPerPage y filterParams como argumentos separados
  if (typeof paramsOrPage === 'number') {
    const page = paramsOrPage;
    const pageSize = itemsPerPage || 20;
    const filters = filterParams || {};
    return studentsApi.list({
      page,
      page_size: pageSize,
      ...filters,
    });
  }
  return studentsApi.list(paramsOrPage);
}
export const getStudent = studentsApi.get;
export const createStudent = studentsApi.create;
export const updateStudent = studentsApi.update;
export const getCareers = academicsApi.getCareers;

// Academic functions
export const getStudentProgress = studentsApi.getProgress;
export const getCareerPensum = academicsApi.getPensum;
export const getCourses = academicsApi.getCourses;
export const getCourseEnrollments = (studentId?: string | number | any) => {
  if (typeof studentId === 'string' || typeof studentId === 'number') {
    // Si se pasa studentId directamente, usar el endpoint by_student
    return api.get('/academics/enrollments/by_student/', { params: { student_id: studentId } });
  }
  // Si se pasa un objeto con params
  return academicsApi.getEnrollments(studentId);
};
export const createCourseEnrollment = academicsApi.createCourseEnrollment;
export const updateCourseGrade = academicsApi.updateGrade;

// Payment functions
export function getPayments(pageOrParams?: number | any, itemsPerPage?: number, filterParams?: any) {
  // Compatibilidad: si se pasa page, itemsPerPage y filterParams como argumentos separados
  if (typeof pageOrParams === 'number') {
    const page = pageOrParams;
    const pageSize = itemsPerPage || 20;
    const filters = filterParams || {};
    return paymentsApi.list({
      page,
      page_size: pageSize,
      ...filters,
    });
  }
  return paymentsApi.list(pageOrParams);
}
export const createPayment = paymentsApi.create;
export const approvePayment = paymentsApi.approve;
export const rejectPayment = paymentsApi.reject;
export const uploadPaymentReceipt = paymentsApi.uploadReceipt;
export const updatePaymentReference = paymentsApi.updateReference;
export const getPendingPaymentsCount = paymentsApi.getPendingCount;
export const getPaymentTypes = paymentTypesApi.list;
export const getStudentByCarnet = (carnet: string) => 
  api.get('/payments/public/student/', { params: { carnet } });
export const createPaymentIntent = paymentsApi.createPaymentIntent;
export const processPublicPayment = paymentsApi.processPublicPayment;

// Scholarship functions
export const getScholarships = scholarshipsApi.list;
export const createScholarship = scholarshipsApi.create;

// Document functions
export const getStudentDocuments = (studentId: string | number) => 
  documentsApi.getByStudent(studentId);
export const uploadDocument = async (studentId: string | number, documentType: string, file: File) => {
  // First, get all documents for the student
  const documentsResponse = await documentsApi.getByStudent(studentId);
  const documents = documentsResponse.data.results || documentsResponse.data || [];
  
  // Find the document with the matching document_type
  const document = documents.find((doc: any) => doc.document_type === documentType);
  
  if (!document) {
    throw new Error(`No se encontró un documento de tipo ${documentType} para el estudiante`);
  }
  
  // Upload the file to the found document
  return documentsApi.uploadFile(document.id, file);
};
export const updateDocumentStatus = documentsApi.updateStatus;

// Enrollment functions
export const getEnrollment = enrollmentsApi.get;
export const generateContract = enrollmentsApi.generateContract;

// Thesis functions
export const getThesis = (studentId?: string | number) => {
  if (studentId) {
    return academicsApi.getThesisByStudent(studentId);
  }
  return academicsApi.getThesis();
};
export const updateThesisStatus = academicsApi.updateThesisStatus;

// Reports API
export const reportsApi = {
  getOverview: (params?: { start_date?: string; end_date?: string }) =>
    api.get('/reports/overview/', { params }),
  getStudentsReport: (params?: { start_date?: string; end_date?: string }) =>
    api.get('/reports/students/', { params }),
  getPaymentsReport: (params?: { start_date?: string; end_date?: string }) =>
    api.get('/reports/payments/', { params }),
  getAcademicsReport: (params?: { start_date?: string; end_date?: string }) =>
    api.get('/reports/academics/', { params }),
  getScholarshipsReport: (params?: { start_date?: string; end_date?: string }) =>
    api.get('/reports/scholarships/', { params }),
};


