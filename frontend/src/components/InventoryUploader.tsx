import React, { useRef, useState } from 'react';
import {
  UploadCloud,
  FileSpreadsheet,
  Play,
  CheckCircle,
  RefreshCw,
} from 'lucide-react';
import { Recall } from '../types';

interface InventoryUploaderProps {
  selectedRecall: Recall | null;
  onAuditStart: (file: File) => void;
  loading: boolean;
}

// Preset sample synthetic hospital CSV content for instant demo.
// SYN-2011 intentionally has manufacturer/product-family information
// but no deterministic identifiers, so it should become NEEDS REVIEW.
const SAMPLE_CSV_CONTENT = `inventory_id,manufacturer,product_name,model,catalog_number,udi_di,lot_number,serial_number,quantity,location
INV-1001,Medtronic Inc.,Heartware Ventricular Assist System,HVAD-100,HV-100-REF,00643169876543,LOT-2023-A99,SN-884920,5,ICU West - Storage Bay 2
INV-1002,Medtronic Inc.,Heartware Ventricular Assist Controller,HVAD-CTRL,HV-CTRL-200,00643169876544,LOT-2023-B12,SN-991204,3,Cardiovascular Surgery OR-4
INV-1003,Abbott Laboratories,HeartMate 3 Left Ventricular Assist System,HM3-1000,HM3-CAT-10,00884992110293,LOT-HM-7788,SN-HM3-5521,2,Cardiac Care Unit 3B
INV-1004,Abbott Medical,HeartMate Touch Communication System,HM-TOUCH,HM-T-300,00884992110300,LOT-HM-9900,SN-HM3-9912,4,Medical Equipment Central Depot
INV-1005,Baxter Healthcare,Spectrum IQ Infusion Pump,SPEC-IQ-200,IQ-200-PUMP,00732890123456,LOT-BX-4451,SN-PUMP-1092,12,General Medical Ward - Floor 4
INV-1006,Baxter Healthcare,Spectrum Pump Battery Pack,SPEC-BAT,IQ-BAT-50,00732890123457,LOT-BX-5599,SN-BAT-0922,25,Central Equipment Room
INV-1007,Philips Medical Systems,HeartStart XL Defibrillator,M4735A,M4735A-OPT,00884838291029,LOT-PH-1029,SN-DEF-38910,8,Emergency Dept - Trauma Bay 1
INV-1008,Stryker Corporation,LIFEPAK 15 Monitor/Defibrillator,LP15-DEF,99577-000001,00762819201928,LOT-ST-8812,SN-LP-44102,6,Emergency Dept - Resus Room
INV-1011,Becton Dickinson (BD),Alaris System Infusion Pump Module,8100,8100-0003,00382901928374,LOT-BD-1100,SN-AL-8100-449,18,Pediatric Intensive Care Unit
INV-1014,General Hospital Supplies,Standard IV Pole Heavy Duty,IVP-HD,POLE-100,00112233445566,LOT-GEN-01,SN-GEN-POLE-01,50,Central Warehouse Bay A
SYN-2011,"Smith & Nephew, Inc.","JOURNEY BCS Knee CoCr Femoral Component","Journey BCS",,,,1,"Orthopedic OR - Manual Review Shelf"`;

export const InventoryUploader: React.FC<InventoryUploaderProps> = ({
  selectedRecall,
  onAuditStart,
  loading,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleLoadSample = () => {
    const blob = new Blob([SAMPLE_CSV_CONTENT], {
      type: 'text/csv',
    });

    const file = new File(
      [blob],
      'hospital_inventory_sample.csv',
      { type: 'text/csv' }
    );

    setSelectedFile(file);
  };

  const handleRunAudit = () => {
    if (selectedFile && selectedRecall) {
      onAuditStart(selectedFile);
    }
  };

  return (
    <div className="glass-panel p-5 rounded-xl border border-slate-800">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <FileSpreadsheet className="w-5 h-5 text-cyan-400" />
            2. Upload Hospital Inventory CSV
          </h2>

          <p className="text-xs text-slate-400 mt-0.5">
            Cross-reference hospital device records with selected FDA recall scope
          </p>
        </div>

        {typeof window !== 'undefined' && window.location.search.includes('demo=true') && (
          <button
            type="button"
            onClick={handleLoadSample}
            className="text-[11px] px-2.5 py-1 rounded bg-slate-800/80 hover:bg-slate-700 text-slate-400 border border-slate-700 transition-colors flex items-center gap-1 font-mono"
          >
            <RefreshCw className="w-3 h-3" />
            Load Sample CSV
          </button>
        )}
      </div>

      <div
        onClick={() => fileInputRef.current?.click()}
        className="border-2 border-dashed border-slate-800 hover:border-cyan-500/60 rounded-xl p-6 text-center cursor-pointer bg-slate-950/40 hover:bg-slate-900/40 transition-all group"
      >
        <input
          type="file"
          accept=".csv"
          ref={fileInputRef}
          onChange={handleFileChange}
          className="hidden"
        />

        <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-slate-900 flex items-center justify-center text-cyan-400 group-hover:scale-110 transition-transform">
          <UploadCloud className="w-6 h-6" />
        </div>

        {selectedFile ? (
          <div className="space-y-1">
            <p className="text-xs font-bold text-cyan-400 flex items-center justify-center gap-1.5">
              <CheckCircle className="w-4 h-4 text-emerald-400" />
              {selectedFile.name}
            </p>

            <p className="text-[11px] text-slate-500">
              {(selectedFile.size / 1024).toFixed(1)} KB • Ready for deterministic verification
            </p>
          </div>
        ) : (
          <div>
            <p className="text-xs font-semibold text-slate-300">
              Click to select hospital inventory CSV or drag and drop
            </p>

            <p className="text-[11px] text-slate-500 mt-1">
              Supports columns: manufacturer, product_name, model,
              catalog_number, lot_number, serial_number, udi_di
            </p>
          </div>
        )}
      </div>

      <div className="mt-4 flex items-center justify-between pt-2">
        <span className="text-xs text-slate-400">
          Target Recall:{' '}
          <span className="font-mono text-cyan-400 font-semibold">
            {selectedRecall?.recall_id || 'None selected'}
          </span>
        </span>

        <button
          type="button"
          disabled={!selectedFile || !selectedRecall || loading}
          onClick={handleRunAudit}
          className="px-5 py-2 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 disabled:opacity-50 text-white font-bold text-xs shadow-lg shadow-cyan-950/60 transition-all flex items-center gap-2"
        >
          {loading ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              Running Verification...
            </>
          ) : (
            <>
              <Play className="w-4 h-4 fill-current" />
              Execute Recall Audit
            </>
          )}
        </button>
      </div>
    </div>
  );
};