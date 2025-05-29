import { Link } from 'react-router-dom';

function Navbar() {
  return (
    <nav className="bg-blue-600 text-white shadow-md">
      <div className="container mx-auto px-4 py-3 flex justify-between items-center">
        <div className="flex items-center space-x-2 rtl:space-x-reverse">
          <img 
            src="/images/logo.png" 
            alt="לוגו המערכת" 
            className="h-8 w-auto"
            onError={(e) => {
              // Fallback to text if image fails to load
              e.target.outerHTML = 
                '<div class="h-8 w-8 bg-white text-blue-600 font-bold flex items-center justify-center rounded">ל</div>';
            }}
          />
          <Link to="/" className="text-xl font-bold hover:text-blue-100">
            מערכת קיבוע זכויות
          </Link>
        </div>
        <div className="flex space-x-4 rtl:space-x-reverse">
          <Link 
            to="/" 
            className="px-3 py-2 rounded hover:bg-blue-700 transition-colors flex items-center"
          >
            <span className="ml-1">🏠</span>
            <span>בית</span>
          </Link>
        </div>
      </div>
    </nav>
  );
}

export default Navbar;
