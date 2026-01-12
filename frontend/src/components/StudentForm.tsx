import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { getStudent, createStudent, updateStudent, getCareers, catalogosApi } from '../services/api';
import { FiUser, FiSave, FiX, FiLoader } from '../utils/icons';
import { useToast } from '../hooks/useToast';
import './shared.css';
import './StudentForm.css';

interface Career {
  id: string;
  name: string;
}

interface CatalogoItem {
  id: string;
  codigo?: string;
  nombre: string;
}

const StudentForm: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const { success, error } = useToast();
  const isEdit = !!id;

  const [student, setStudent] = useState({
    first_name: '',
    first_last_name: '',
    second_last_name: '',
    email: '',
    phone: '+52',
    date_of_birth: '',
    gender: 'H',
    curp: '',
    address: '',
    birth_country: '',
    birth_state: '',
    origin_country: '',
    native_language: '',
    special_educational_need: '',
    academic_background: '',
    career: '',
    scholarship_type: 'NINGUNA',
  });

  const [careers, setCareers] = useState<Career[]>([]);
  const [catalogos, setCatalogos] = useState({
    paises: [] as CatalogoItem[],
    entidades: [] as CatalogoItem[],
    idiomas: [] as CatalogoItem[],
    necesidades: [] as CatalogoItem[],
    antecedentes: [] as CatalogoItem[],
  });
  const [entidadesFiltradas, setEntidadesFiltradas] = useState<CatalogoItem[]>([]);
  const [loadingEntidades, setLoadingEntidades] = useState(false);

  const [loading, setLoading] = useState(false);
  const [loadingData, setLoadingData] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    loadInitialData();
    if (isEdit && id) {
      loadStudent(id);
    }
  }, [id, isEdit]);

  // Cargar entidades federativas cuando cambia el país de nacimiento
  useEffect(() => {
    const paisId = student.birth_country;
    if (paisId) {
      loadEntidadesFederativas(paisId);
    } else {
      setEntidadesFiltradas([]);
      setStudent(prev => ({ ...prev, birth_state: '' }));
    }
  }, [student.birth_country]); // eslint-disable-line react-hooks/exhaustive-deps

  const loadInitialData = async () => {
    try {
      await Promise.all([
        loadCareers(),
        loadCatalogos(),
      ]);
    } catch (err) {
      console.error('Error loading initial data:', err);
    }
  };

  const loadCareers = async () => {
    try {
      const response = await getCareers();
      const data = response.data.results || response.data;
      setCareers(data);
    } catch (err) {
      console.error('Error loading careers:', err);
    }
  };

  const loadCatalogos = async () => {
    try {
      const [paisesRes, idiomasRes, necesidadesRes, antecedentesRes] = await Promise.all([
        catalogosApi.getPaises(),
        catalogosApi.getIdiomas(),
        catalogosApi.getNecesidadesEducativas(),
        catalogosApi.getAntecedentesAcademicos(),
      ]);

      setCatalogos({
        paises: paisesRes.data.results || paisesRes.data || [],
        entidades: [], // Ya no se cargan todas, solo cuando se selecciona un país
        idiomas: idiomasRes.data.results || idiomasRes.data || [],
        necesidades: necesidadesRes.data.results || necesidadesRes.data || [],
        antecedentes: antecedentesRes.data.results || antecedentesRes.data || [],
      });
    } catch (err) {
      console.error('Error loading catalogos:', err);
    }
  };

  const loadEntidadesFederativas = async (paisId: string) => {
    if (!paisId) {
      setEntidadesFiltradas([]);
      return;
    }

    setLoadingEntidades(true);
    try {
      // Asegurarse de que el parámetro se pase correctamente
      const response = await catalogosApi.getEntidadesFederativas({ pais: paisId });
      
      // Manejar diferentes formatos de respuesta
      let entidades = [];
      if (Array.isArray(response.data)) {
        entidades = response.data;
      } else if (response.data?.results) {
        entidades = response.data.results;
      } else if (response.data?.data) {
        entidades = response.data.data;
      }
      
      // El backend ya filtra por is_active=True, así que no necesitamos filtrar aquí
      setEntidadesFiltradas(entidades);
      
      // Si el birth_state actual no está en las nuevas entidades, limpiarlo
      setStudent(prev => {
        if (prev.birth_state && !entidades.find((e: CatalogoItem) => e.id === prev.birth_state)) {
          return { ...prev, birth_state: '' };
        }
        return prev;
      });
    } catch (err: any) {
      console.error('Error loading entidades federativas:', err);
      console.error('Error details:', err.response?.data || err.message);
      error('Error al cargar las entidades federativas. Por favor, intente nuevamente.');
      setEntidadesFiltradas([]);
    } finally {
      setLoadingEntidades(false);
    }
  };

  const loadStudent = async (studentId: string) => {
    setLoadingData(true);
    try {
      const response = await getStudent(studentId);
      const data = response.data;
      const studentData = {
        first_name: data.first_name || '',
        first_last_name: data.first_last_name || data.last_name || '',
        second_last_name: data.second_last_name || '',
        email: data.email || '',
        phone: data.phone && data.phone.startsWith('+52') ? data.phone : '+52' + (data.phone ? data.phone.replace('+52', '').replace(/\D/g, '').slice(0, 10) : ''),
        date_of_birth: data.date_of_birth || '',
        gender: data.gender || 'H',
        curp: data.curp || '',
        address: data.address || '',
        birth_country: data.birth_country || '',
        birth_state: data.birth_state || '',
        origin_country: data.origin_country || '',
        native_language: data.native_language || '',
        special_educational_need: data.special_educational_need || '',
        academic_background: data.academic_background || '',
        career: data.career || '',
        scholarship_type: data.scholarship_type || 'NINGUNA',
      };
      setStudent(studentData);
      
      // Cargar entidades federativas si hay país de nacimiento
      if (studentData.birth_country) {
        await loadEntidadesFederativas(studentData.birth_country);
      }
    } catch (err: any) {
      console.error('Error loading student:', err);
      error('Error al cargar estudiante');
    } finally {
      setLoadingData(false);
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!student.first_name.trim()) {
      newErrors.first_name = 'El nombre es requerido';
    } else if (student.first_name.length > 70) {
      newErrors.first_name = 'El nombre no debe exceder 70 caracteres';
    }
    
    if (!student.first_last_name.trim()) {
      newErrors.first_last_name = 'El primer apellido es requerido';
    } else if (student.first_last_name.length > 70) {
      newErrors.first_last_name = 'El primer apellido no debe exceder 70 caracteres';
    }
    
    if (student.second_last_name && student.second_last_name.length > 70) {
      newErrors.second_last_name = 'El segundo apellido no debe exceder 70 caracteres';
    }
    
    if (!student.email.trim()) {
      newErrors.email = 'El email es requerido';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(student.email)) {
      newErrors.email = 'El email no es válido';
    }
    
    // Validar teléfono: debe tener +52 + 10 dígitos
    const phoneDigits = student.phone.replace('+52', '').trim();
    if (!phoneDigits) {
      newErrors.phone = 'El teléfono es requerido. Ingrese 10 dígitos después de +52';
    } else if (phoneDigits.length !== 10) {
      newErrors.phone = `Debe ingresar exactamente 10 dígitos. Se encontraron ${phoneDigits.length} dígitos.`;
    } else if (!/^\d+$/.test(phoneDigits)) {
      newErrors.phone = 'Solo se permiten números';
    } else {
      // Validar que el código de área (LADA) sea válido
      const lada = phoneDigits.substring(0, 2);
      if (parseInt(lada[0]) < 2) {
        newErrors.phone = 'El código de área (LADA) no es válido. Debe comenzar con 2-9';
      }
    }
    
    if (!student.date_of_birth) {
      newErrors.date_of_birth = 'La fecha de nacimiento es requerida';
    }
    
    if (!student.gender) {
      newErrors.gender = 'El género es requerido';
    }
    
    if (!student.curp.trim()) {
      newErrors.curp = 'El CURP es requerido';
    } else {
      const curp = student.curp.trim().toUpperCase();
      // Verificar longitud
      if (curp.length !== 18) {
        newErrors.curp = `El CURP debe tener exactamente 18 caracteres. Se encontraron ${curp.length} caracteres.`;
      } else {
        // Verificar formato: 4 letras + 6 dígitos + H/M + 5 letras + 1 alfanumérico + 1 dígito
        const curpPattern = /^[A-Z]{4}\d{6}[HM][A-Z]{5}[0-9A-Z]\d$/;
        if (!curpPattern.test(curp)) {
          newErrors.curp = 'Formato de CURP inválido. Debe tener: 4 letras + 6 dígitos + H o M + 5 letras + 1 alfanumérico + 1 dígito. Ejemplo: ABCD123456HHIJKLM01';
        }
      }
    }
    
    if (!student.birth_country) {
      newErrors.birth_country = 'El país de nacimiento es requerido';
    }
    
    if (!student.address.trim()) {
      newErrors.address = 'La dirección es requerida';
    }
    
    if (!student.career) {
      newErrors.career = 'La carrera es requerida';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setLoading(true);
    setErrors({});

    try {
      // Preparar datos para enviar (convertir campos vacíos a null para campos opcionales)
      const submitData: any = {
        first_name: student.first_name.trim(),
        first_last_name: student.first_last_name?.trim() || null,
        second_last_name: student.second_last_name?.trim() || null,
        email: student.email.trim(),
        phone: student.phone.trim(),
        date_of_birth: student.date_of_birth,
        gender: student.gender,
        curp: student.curp.trim().toUpperCase(),
        address: student.address.trim(),
        birth_country: student.birth_country || null,
        birth_state: student.birth_state || null,
        origin_country: student.origin_country || null,
        native_language: student.native_language || null,
        special_educational_need: student.special_educational_need || null,
        academic_background: student.academic_background || null,
        career: student.career,
        scholarship_type: student.scholarship_type,
      };

      // Remover campos null/undefined vacíos para evitar enviar strings vacíos
      Object.keys(submitData).forEach(key => {
        if (submitData[key] === '' || submitData[key] === undefined) {
          submitData[key] = null;
        }
      });

      console.log('Enviando datos:', submitData);

      if (isEdit && id) {
        await updateStudent(id, submitData);
        success('Estudiante actualizado exitosamente');
        setTimeout(() => navigate('/students'), 1000);
      } else {
        const response = await createStudent(submitData);
        const createdStudent = response.data;
        
        // Verificar si el contrato fue generado
        const contractGenerated = createdStudent.enrollment?.contract_generated || false;
        const contractMessage = contractGenerated 
          ? 'Estudiante creado exitosamente. Contrato generado automáticamente.' 
          : 'Estudiante creado exitosamente.';
        
        success(contractMessage);
        
        // Navegar al detalle del estudiante para ver el contrato
        if (createdStudent.id) {
          setTimeout(() => navigate(`/students/${createdStudent.id}`), 1500);
        } else {
          setTimeout(() => navigate('/students'), 1000);
        }
      }
    } catch (err: any) {
      console.error('Error saving student:', err);
      console.error('Error response:', err.response?.data);
      
      if (err.response?.data) {
        const errorData = err.response.data;
        setErrors(errorData);
        
        // Mostrar todos los errores de validación
        let errorMessages: string[] = [];
        
        if (errorData.detail) {
          errorMessages.push(errorData.detail);
        } else {
          // Recopilar todos los errores de campos
          Object.keys(errorData).forEach(key => {
            const fieldError = errorData[key];
            if (Array.isArray(fieldError)) {
              errorMessages.push(`${key}: ${fieldError.join(', ')}`);
            } else if (typeof fieldError === 'string') {
              errorMessages.push(`${key}: ${fieldError}`);
            } else if (typeof fieldError === 'object') {
              errorMessages.push(`${key}: ${JSON.stringify(fieldError)}`);
            }
          });
        }
        
        const errorMessage = errorMessages.length > 0 
          ? errorMessages.join(' | ') 
          : 'Error al guardar estudiante';
        error(errorMessage);
      } else {
        error('Error al guardar estudiante. Por favor, verifique los datos e intente nuevamente.');
      }
    } finally {
      setLoading(false);
    }
  };

  if (loadingData) {
    return (
      <div className="page-container">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Cargando datos del estudiante...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <div className="header-title">
          <FiUser className="header-icon" />
          <div>
            <h1>{isEdit ? 'Editar Estudiante' : 'Nuevo Estudiante'}</h1>
            <p className="header-subtitle">
              {isEdit ? 'Modifica la información del estudiante' : 'Registra un nuevo estudiante con datos SEP'}
            </p>
          </div>
        </div>
      </div>

      <div className="card">
        <form onSubmit={handleSubmit} className="student-form">
          {/* Sección 1: Información Personal Básica - SEP */}
          <div className="form-section">
            <h3 className="section-title">Información Personal - SEP</h3>
            <div className="form-row">
              <div className="form-group">
                <label>Nombre(s) del alumno * (máx. 70 caracteres)</label>
                <input
                  type="text"
                  value={student.first_name}
                  onChange={(e) => setStudent({ ...student, first_name: e.target.value })}
                  className={errors.first_name ? 'error' : ''}
                  maxLength={70}
                  required
                  placeholder="Como aparece en acta de nacimiento"
                />
                {errors.first_name && <span className="error-message">{errors.first_name}</span>}
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Primer apellido * (máx. 70 caracteres)</label>
                <input
                  type="text"
                  value={student.first_last_name}
                  onChange={(e) => setStudent({ ...student, first_last_name: e.target.value })}
                  className={errors.first_last_name ? 'error' : ''}
                  maxLength={70}
                  required
                  placeholder="Conforme al acta de nacimiento"
                />
                {errors.first_last_name && <span className="error-message">{errors.first_last_name}</span>}
              </div>
              
              <div className="form-group">
                <label>Segundo apellido (máx. 70 caracteres, opcional)</label>
                <input
                  type="text"
                  value={student.second_last_name}
                  onChange={(e) => setStudent({ ...student, second_last_name: e.target.value })}
                  className={errors.second_last_name ? 'error' : ''}
                  maxLength={70}
                  placeholder="Dejar en blanco si no cuenta con segundo apellido"
                />
                {errors.second_last_name && <span className="error-message">{errors.second_last_name}</span>}
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Fecha de nacimiento *</label>
                <input
                  type="date"
                  value={student.date_of_birth}
                  onChange={(e) => setStudent({ ...student, date_of_birth: e.target.value })}
                  className={errors.date_of_birth ? 'error' : ''}
                  required
                />
                {errors.date_of_birth && <span className="error-message">{errors.date_of_birth}</span>}
              </div>
              
              <div className="form-group">
                <label>Género *</label>
                <select
                  value={student.gender}
                  onChange={(e) => setStudent({ ...student, gender: e.target.value })}
                  className={errors.gender ? 'error' : ''}
                  required
                >
                  <option value="H">Hombre</option>
                  <option value="M">Mujer</option>
                </select>
                {errors.gender && <span className="error-message">{errors.gender}</span>}
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>CURP del alumno * (18 caracteres)</label>
                <input
                  type="text"
                  value={student.curp}
                  onChange={(e) => setStudent({ ...student, curp: e.target.value.toUpperCase() })}
                  maxLength={18}
                  className={errors.curp ? 'error' : ''}
                  required
                  placeholder="ABCD123456HHIJKLM01"
                />
                <small style={{ display: 'block', marginTop: '0.25rem', color: '#666', fontSize: '0.8125rem' }}>
                  Formato: 4 letras + 6 dígitos + H/M + 5 letras + 1 alfanumérico + 1 dígito
                </small>
                {errors.curp && <span className="error-message">{errors.curp}</span>}
              </div>
            </div>
          </div>

          {/* Sección 2: Lugar de Nacimiento - SEP */}
          <div className="form-section">
            <h3 className="section-title">Lugar de Nacimiento - SEP</h3>
            <div className="form-row">
              <div className="form-group">
                <label>País de nacimiento *</label>
                <select
                  value={student.birth_country}
                  onChange={(e) => setStudent({ ...student, birth_country: e.target.value, birth_state: '' })}
                  className={errors.birth_country ? 'error' : ''}
                  required
                >
                  <option value="">Seleccione un país</option>
                  {catalogos.paises.map((pais) => (
                    <option key={pais.id} value={pais.id}>
                      {pais.nombre}
                    </option>
                  ))}
                </select>
                {errors.birth_country && <span className="error-message">{errors.birth_country}</span>}
              </div>
              
              <div className="form-group">
                <label>Entidad federativa o ciudad de nacimiento</label>
                <select
                  value={student.birth_state}
                  onChange={(e) => setStudent({ ...student, birth_state: e.target.value })}
                  disabled={!student.birth_country || loadingEntidades}
                  className={loadingEntidades ? 'loading' : ''}
                >
                  <option value="">
                    {loadingEntidades 
                      ? 'Cargando entidades...' 
                      : !student.birth_country 
                        ? 'Primero seleccione un país' 
                        : entidadesFiltradas.length === 0
                          ? 'No hay entidades disponibles'
                          : 'Seleccione una entidad'}
                  </option>
                  {entidadesFiltradas.map((entidad) => (
                    <option key={entidad.id} value={entidad.id}>
                      {entidad.nombre}
                    </option>
                  ))}
                </select>
                {loadingEntidades && <small style={{ color: 'var(--gray-500)' }}>Cargando entidades del país seleccionado...</small>}
                {student.birth_country && !loadingEntidades && entidadesFiltradas.length === 0 && (
                  <small style={{ color: 'var(--warning-color, #f59e0b)' }}>
                    No hay entidades registradas para este país. Por favor, ejecute el comando de seed o verifique que el país tenga estados/ciudades configuradas.
                  </small>
                )}
              </div>
            </div>
          </div>

          {/* Sección 3: Información Adicional - SEP (Opcional) */}
          <div className="form-section">
            <h3 className="section-title">Información Adicional - SEP (Opcional)</h3>
            <div className="form-row">
              <div className="form-group">
                <label>País de procedencia</label>
                <select
                  value={student.origin_country}
                  onChange={(e) => setStudent({ ...student, origin_country: e.target.value })}
                >
                  <option value="">Ninguno (no aplica)</option>
                  {catalogos.paises.map((pais) => (
                    <option key={pais.id} value={pais.id}>
                      {pais.nombre}
                    </option>
                  ))}
                </select>
                <small>Únicamente si realizó estudios previos en dicho país</small>
              </div>
              
              <div className="form-group">
                <label>Idioma o lengua natural del alumno</label>
                <select
                  value={student.native_language}
                  onChange={(e) => setStudent({ ...student, native_language: e.target.value })}
                >
                  <option value="">Seleccione un idioma</option>
                  {catalogos.idiomas.map((idioma) => (
                    <option key={idioma.id} value={idioma.id}>
                      {idioma.nombre}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Necesidad educativa especial</label>
                <select
                  value={student.special_educational_need}
                  onChange={(e) => setStudent({ ...student, special_educational_need: e.target.value })}
                >
                  <option value="">Ninguna</option>
                  {catalogos.necesidades.map((necesidad) => (
                    <option key={necesidad.id} value={necesidad.id}>
                      {necesidad.nombre}
                    </option>
                  ))}
                </select>
                <small>En caso de discapacidad o aptitudes sobresalientes</small>
              </div>
              
              <div className="form-group">
                <label>Presenta antecedente académico</label>
                <select
                  value={student.academic_background}
                  onChange={(e) => setStudent({ ...student, academic_background: e.target.value })}
                >
                  <option value="">Seleccione un antecedente</option>
                  {catalogos.antecedentes.map((antecedente) => (
                    <option key={antecedente.id} value={antecedente.id}>
                      {antecedente.nombre}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Sección 4: Información de Contacto */}
          <div className="form-section">
            <h3 className="section-title">Información de Contacto</h3>
            <div className="form-row">
              <div className="form-group">
                <label>Email *</label>
                <input
                  type="email"
                  value={student.email}
                  onChange={(e) => setStudent({ ...student, email: e.target.value })}
                  className={errors.email ? 'error' : ''}
                  required
                />
                {errors.email && <span className="error-message">{errors.email}</span>}
              </div>
              
              <div className="form-group">
                <label>Teléfono *</label>
                <div style={{ display: 'flex', alignItems: 'center' }}>
                  <span style={{ 
                    padding: '0.875rem 1rem', 
                    border: `2px solid ${errors.phone ? 'var(--danger-color)' : 'var(--gray-300)'}`, 
                    borderRight: 'none',
                    borderTopLeftRadius: 'var(--radius-md)',
                    borderBottomLeftRadius: 'var(--radius-md)',
                    background: 'var(--gray-100)',
                    color: 'var(--gray-700)',
                    fontWeight: 600,
                    userSelect: 'none'
                  }}>+52</span>
                  <input
                    type="tel"
                    value={student.phone.startsWith('+52') ? student.phone.replace('+52', '') : student.phone.replace(/\D/g, '').slice(0, 10)}
                    onChange={(e) => {
                      // Solo permitir números, máximo 10 dígitos
                      const value = e.target.value.replace(/\D/g, '').slice(0, 10);
                      setStudent({ ...student, phone: '+52' + value });
                    }}
                    className={errors.phone ? 'error' : ''}
                    placeholder="5512345678"
                    maxLength={10}
                    required
                    style={{
                      borderTopLeftRadius: 0,
                      borderBottomLeftRadius: 0,
                      flex: 1
                    }}
                  />
                </div>
                <small style={{ display: 'block', marginTop: '0.25rem', color: '#666', fontSize: '0.8125rem' }}>
                  Ingrese 10 dígitos (ejemplo: 5512345678)
                </small>
                {errors.phone && <span className="error-message">{errors.phone}</span>}
              </div>
            </div>
            
            <div className="form-group">
              <label>Dirección *</label>
              <textarea
                value={student.address}
                onChange={(e) => setStudent({ ...student, address: e.target.value })}
                className={errors.address ? 'error' : ''}
                required
                rows={3}
                placeholder="Calle, número, colonia, ciudad, estado"
              />
              {errors.address && <span className="error-message">{errors.address}</span>}
            </div>
          </div>

          {/* Sección 5: Información Académica */}
          <div className="form-section">
            <h3 className="section-title">Información Académica</h3>
            <div className="form-row">
              <div className="form-group">
                <label>Carrera *</label>
                <select
                  value={student.career}
                  onChange={(e) => setStudent({ ...student, career: e.target.value })}
                  className={errors.career ? 'error' : ''}
                  required
                >
                  <option value="">Seleccione una carrera</option>
                  {careers.map((career) => (
                    <option key={career.id} value={career.id}>
                      {career.name}
                    </option>
                  ))}
                </select>
                {errors.career && <span className="error-message">{errors.career}</span>}
              </div>
              
              <div className="form-group">
                <label>Tipo de Beca</label>
                <select
                  value={student.scholarship_type}
                  onChange={(e) => setStudent({ ...student, scholarship_type: e.target.value })}
                >
                  <option value="NINGUNA">Sin Beca</option>
                  <option value="COMPLETA">Beca Completa</option>
                  <option value="MEDIA">Media Beca</option>
                </select>
              </div>
            </div>
          </div>

          <div className="form-actions">
            <button type="submit" className="btn btn-primary btn-large" disabled={loading}>
              {loading ? (
                <>
                  <FiLoader className="spinning" /> Guardando...
                </>
              ) : (
                <>
                  <FiSave /> {isEdit ? 'Actualizar' : 'Crear'} Estudiante
                </>
              )}
            </button>
            <button type="button" className="btn btn-secondary btn-large" onClick={() => navigate('/students')}>
              <FiX /> Cancelar
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default StudentForm;
