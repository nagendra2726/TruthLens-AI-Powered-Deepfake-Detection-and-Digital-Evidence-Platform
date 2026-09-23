// frontend/src/utils/exportUtils.js
import jsPDF from 'jspdf';
import { formatProbability } from './formatters';

export const exportResults = (result, fileName) => {
  const dataStr = JSON.stringify(result, null, 2);
  const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);
  
  const exportFileDefaultName = `truthlens_analysis_${fileName}_${new Date().toISOString().slice(0, 10)}.json`;
  
  const linkElement = document.createElement('a');
  linkElement.setAttribute('href', dataUri);
  linkElement.setAttribute('download', exportFileDefaultName);
  linkElement.click();
};

export const downloadPDF = (result, fileName, preview, customDocket = null) => {
  const pdf = new jsPDF();
  
  // Resolve docket information
  let docket = customDocket || result?.assessment?.incident_docket;
  if (!docket && fileName) {
    try {
      const stored = localStorage.getItem(`truthlens_docket_${fileName}`);
      if (stored) docket = JSON.parse(stored);
    } catch (_) {}
  }

  // Header
  pdf.setFontSize(20);
  pdf.setFont('helvetica', 'bold');
  pdf.setTextColor(30, 64, 175); // Primary blue
  pdf.text('TruthLens Analysis Report', 20, 20);
  
  // Metadata
  pdf.setFont('helvetica', 'normal');
  pdf.setFontSize(9);
  pdf.setTextColor(100);
  pdf.text(`Generated: ${new Date().toLocaleString()}`, 20, 28);
  pdf.text(`Case / File: ${fileName || result?.case_id || 'analysis'}`, 20, 34);
  pdf.text(`Request ID: ${result?.request_id || result?.id || 'N/A'}`, 20, 40);
  
  // Main verdict banner
  pdf.setFontSize(15);
  pdf.setFont('helvetica', 'bold');
  const isDeepfake = result?.is_likely_deepfake || (result?.assessment?.risk_level === 'HIGH') || ((result?.suspected_analysis?.ai_probability || 0) > 0.5);
  const verdictColor = isDeepfake ? [220, 38, 38] : [34, 197, 94];
  pdf.setTextColor(...verdictColor);
  
  const catLabel = result?.assessment?.category
    ? result.assessment.category.replace(/_/g, ' ')
    : (isDeepfake ? 'LIKELY AI-GENERATED' : 'LIKELY AUTHENTIC');
  pdf.text(catLabel.toUpperCase(), 20, 52);
  
  // Details
  pdf.setFont('helvetica', 'normal');
  pdf.setFontSize(10);
  pdf.setTextColor(50);
  
  const prob = result?.deepfake_probability ?? result?.suspected_analysis?.ai_probability ?? 0;
  pdf.text(`AI Probability: ${(prob * 100).toFixed(1)}%`, 20, 61);
  pdf.text(`Risk Level: ${result?.assessment?.risk_level || (isDeepfake ? 'HIGH' : 'LOW')}`, 20, 68);
  pdf.text(`Confidence: ${result?.assessment?.confidence || 'HIGH'}`, 20, 75);
  
  let currentY = 86;

  // ── Incident Docket Section (if provided) ──
  if (docket && (docket.incident_category || docket.circulated_platform || docket.incident_narrative || docket.demands_record || docket.suspect_identifier)) {
    pdf.setFont('helvetica', 'bold');
    pdf.setFontSize(12);
    pdf.setTextColor(30, 64, 175);
    pdf.text('Incident Context & Official Docket', 20, currentY);
    currentY += 6;

    pdf.setFont('helvetica', 'normal');
    pdf.setFontSize(9);
    pdf.setTextColor(60);

    if (docket.incident_category) {
      pdf.text(`• Incident Category: ${docket.incident_category}`, 22, currentY);
      currentY += 5;
    }
    if (docket.circulated_platform) {
      pdf.text(`• Circulated Platform: ${docket.circulated_platform}`, 22, currentY);
      currentY += 5;
    }
    if (docket.incident_date) {
      pdf.text(`• Date Encountered: ${docket.incident_date}`, 22, currentY);
      currentY += 5;
    }
    if (docket.suspect_identifier) {
      pdf.text(`• Suspect Handle / Phone: ${docket.suspect_identifier}`, 22, currentY);
      currentY += 5;
    }
    if (docket.demands_record) {
      pdf.setFont('helvetica', 'bold');
      pdf.setTextColor(180, 83, 9);
      pdf.text(`• Extortion / Demands:`, 22, currentY);
      pdf.setFont('helvetica', 'normal');
      currentY += 4.5;
      const splitDemands = pdf.splitTextToSize(String(docket.demands_record), 165);
      pdf.text(splitDemands, 26, currentY);
      currentY += (splitDemands.length * 4.5);
    }
    if (docket.incident_narrative) {
      pdf.setFont('helvetica', 'bold');
      pdf.setTextColor(50);
      pdf.text(`• Incident Narrative:`, 22, currentY);
      pdf.setFont('helvetica', 'normal');
      currentY += 4.5;
      const splitNarrative = pdf.splitTextToSize(String(docket.incident_narrative), 165);
      pdf.text(splitNarrative, 26, currentY);
      currentY += (splitNarrative.length * 4.5);
    }
    currentY += 4;
  }

  // Model results
  if (result?.model_results && currentY < 230) {
    pdf.setFont('helvetica', 'bold');
    pdf.setFontSize(11);
    pdf.setTextColor(30, 64, 175);
    pdf.text('Model Detection Breakdown', 20, currentY);
    currentY += 6;
    
    pdf.setFont('helvetica', 'normal');
    pdf.setFontSize(9);
    pdf.setTextColor(50);
    
    Object.entries(result.model_results).forEach(([model, res]) => {
      if (!res.error && currentY < 250) {
        pdf.text(`${model}: ${res.class?.toUpperCase() || ''} (${formatProbability(res.probability || 0)})`, 24, currentY);
        currentY += 5.5;
      }
    });
  }
  
  // Add image if preview available
  if (preview) {
    try {
      pdf.addImage(preview, 'JPEG', 130, 25, 60, 50);
    } catch (error) {
      console.error('Error adding image to PDF:', error);
    }
  }
  
  // Legal notice & Footer
  pdf.setFont('helvetica', 'normal');
  pdf.setFontSize(7.5);
  pdf.setTextColor(140);
  pdf.text('Relevant Legal Framework: IT Act 2000 (Sec 66D, 66E, 67A) & Bharatiya Nyaya Sanhita (Sec 318, 308). Helpline: 1930', 20, 280);
  pdf.text('Generated by TruthLens — AI-Powered Deepfake Detection & Digital Evidence Platform', 20, 286);
  
  // Save the PDF
  pdf.save(`truthlens_report_${fileName || 'analysis'}_${new Date().toISOString().slice(0, 10)}.pdf`);
};