import ClientList from '../components/ClientList';

function HomePage() {
  return (
    <div>
      <div className="mb-6">
        <h1 className="text-3xl font-bold">מערכת קיבוע זכויות</h1>
        <p className="text-gray-600">ניהול לקוחות, חישובי פטור והפקת טפסים</p>
      </div>
      
      <ClientList />
    </div>
  );
}

export default HomePage;
