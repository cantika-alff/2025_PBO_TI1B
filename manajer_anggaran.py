import datetime
import pandas as pd
import database  # Import your database module
from model import Transaksi

class AnggaranHarian:
    """Mengelola logika bisnis pengeluaran harian (Repository Pattern)."""
    
    _db_setup_done = False

    def __init__(self):  # perbaikan di sini
        if not AnggaranHarian._db_setup_done:
            print("[AnggaranHarian] Melakukan pengecekan/setup database awal...")
            if database.setup_database_initial():
                AnggaranHarian._db_setup_done = True
                print("[AnggaranHarian] Database siap.")
            else:
                print("[AnggaranHarian] KRITICAL: Setup database awal GAGAL!")

    def tambah_transaksi(self, transaksi) -> bool:
        if not isinstance(transaksi, Transaksi) or transaksi.jumlah <= 0:
            return False
        sql = "INSERT INTO transaksi (deskripsi, jumlah, kategori, tanggal) VALUES (?, ?, ?, ?)"
        params = (transaksi.deskripsi, transaksi.jumlah, transaksi.kategori, transaksi.tanggal.strftime("%Y-%m-%d"))
        last_id = database.execute_query(sql, params)
        if last_id is not None:
            transaksi.id = last_id
            return True
        return False

    def get_dataframe_transaksi(self, filter_tanggal: datetime.date | None = None) -> pd.DataFrame:
        query = "SELECT id, tanggal, kategori, deskripsi, jumlah FROM transaksi"
        params = None
        if filter_tanggal:
            query += " WHERE tanggal = ?"
            params = (filter_tanggal.strftime("%Y-%m-%d"),)
        query += " ORDER BY tanggal DESC, id DESC"
        df = database.get_dataframe(query, params=params)
    
        if not df.empty:
            try:
                import locale
                locale.setlocale(locale.LC_ALL, 'id_ID.UTF-8')
                df['Jumlah (Rp)'] = df['jumlah'].map(lambda x: locale.currency(x or 0, grouping=True, symbol='Rp ')[:-3])
            except:
                df['Jumlah (Rp)'] = df['jumlah'].map(lambda x: f"Rp {x or 0:,.0f}".replace(",", "."))
                df = df[['id', 'tanggal', 'kategori', 'deskripsi', 'Jumlah (Rp)']]  # Pastikan ID ada di sini
        return df

    def hapus_transaksi(self, id_transaksi: int) -> bool:
        """Menghapus transaksi berdasarkan ID."""
        sql = "DELETE FROM transaksi WHERE id = ?"
        params = (id_transaksi,)
        try:
            # Run the delete query
            rows_affected = database.execute_query(sql, params)
            if rows_affected > 0:  # Check if any row was deleted
                return True
            else:
                print(f"Error: No rows affected for ID {id_transaksi}")
                return False
        except Exception as e:
            print(f"Error saat menghapus transaksi: {e}")
            return False
        
    def hitung_total_pengeluaran(self, tanggal=None):
        query = "SELECT SUM(jumlah) as total FROM transaksi"
        params = ()

        if tanggal:
            query += " WHERE tanggal = ?"
            params = (tanggal,)

        result = database.fetch_query(query, params, fetch_all=False)  # ← BENAR

        if result:
            return float(result['total']) if result['total'] else 0.0
        return 0.0

    def get_pengeluaran_per_kategori(self, tanggal=None) -> dict:
        """Mengembalikan pengeluaran total per kategori dalam bentuk dictionary."""
        query = "SELECT kategori, SUM(jumlah) as total FROM transaksi"
        params = ()
        if tanggal:
            query += " WHERE tanggal = ?"
            params = (tanggal,)
        query += " GROUP BY kategori"

        hasil = database.fetch_query(query, params=params, fetch_all=True)
        if not hasil:
            return {}
        return {row["kategori"] or "Tidak Dikategorikan": row["total"] for row in hasil}
