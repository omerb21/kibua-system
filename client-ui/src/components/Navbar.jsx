import { Link } from 'react-router-dom';

function Navbar() {
  return (
    <nav className="bg-blue-600 text-white shadow-md">
      <div className="container mx-auto px-4 py-3 flex justify-between items-center">
        <Link to="/" className="text-xl font-bold">מערכת קיבוע זכויות</Link>
        <div className="flex space-x-4">
          <Link to="/" className="px-3 py-2 rounded hover:bg-blue-700">בית</Link>
        </div>
      </div>
    </nav>
  );
}

export default Navbar;
