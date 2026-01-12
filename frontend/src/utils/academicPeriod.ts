/**
 * Utilidades para períodos académicos
 * 
 * Período 1 (Enero-Abril): Cuatrimestres 1, 4, 7
 * Período 2 (Mayo-Agosto): Cuatrimestres 2, 5, 8
 * Período 3 (Septiembre-Diciembre): Cuatrimestres 3, 6, 9
 */

export function getAcademicPeriod(cuatrimestreNumber: number): number | null {
  const periodMap: { [key: number]: number } = {
    1: 1, 4: 1, 7: 1,
    2: 2, 5: 2, 8: 2,
    3: 3, 6: 3, 9: 3
  };
  return periodMap[cuatrimestreNumber] || null;
}

export function getCuatrimestresByPeriod(period: number): number[] {
  const periodMap: { [key: number]: number[] } = {
    1: [1, 4, 7],
    2: [2, 5, 8],
    3: [3, 6, 9]
  };
  return periodMap[period] || [];
}

export function getPeriodName(period: number): string {
  const periodNames: { [key: number]: string } = {
    1: 'Enero-Abril',
    2: 'Mayo-Agosto',
    3: 'Septiembre-Diciembre'
  };
  return periodNames[period] || `Período ${period}`;
}


