db = db.getSiblingDB('tkr');

db.materi.insertMany([
  {
    id: 1,
    judul: "Memahami Dasar Kendaraan",
    deskripsi: "Modul ini membahas komponen dasar kendaraan ringan."
  },
  {
    id: 17,
    judul: "Memperbaiki Sistem Starter",
    deskripsi: "Modul ini berisi SOP dan teknik dalam memperbaiki sistem starter kendaraan."
  },
  {
    id: 18,
    judul: "Memperbaiki Mesin Kendaraan",
    deskripsi: "Modul ini berisi SOP dan teknik dalam memperbaiki mesin kendaraan."
  }
]);
