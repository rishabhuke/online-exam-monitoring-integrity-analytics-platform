from typing import Optional, Dict, Any
from datetime import datetime

class Candidate:
    """Domain model representing a Candidate in the examination system."""
    
    def __init__(
        self,
        candidate_id: Optional[int],
        name: str,
        email: str,
        password_hash: str,
        photo_path: Optional[str] = None,
        created_at: Optional[datetime] = None
    ) -> None:
        self.candidate_id = candidate_id
        self.name = name
        self.email = email
        self.password_hash = password_hash
        self.photo_path = photo_path
        self.created_at = created_at or datetime.utcnow()

    @classmethod
    def from_db_row(cls, row: Dict[str, Any]) -> 'Candidate':
        """Construct Candidate object from a database query row dictionary."""
        created_at_val = row.get('created_at')
        parsed_created_at = None
        if created_at_val:
            try:
                # SQLite timestamps can be strings, try parsing
                if isinstance(created_at_val, str):
                    parsed_created_at = datetime.fromisoformat(created_at_val)
                else:
                    parsed_created_at = created_at_val
            except ValueError:
                parsed_created_at = datetime.utcnow()
                
        return cls(
            candidate_id=row.get('candidate_id'),
            name=row.get('name', ''),
            email=row.get('email', ''),
            password_hash=row.get('password_hash', ''),
            photo_path=row.get('photo_path'),
            created_at=parsed_created_at
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert Candidate attributes to a JSON-serializable dictionary (excluding sensitive info)."""
        return {
            'candidate_id': self.candidate_id,
            'name': self.name,
            'email': self.email,
            'photo_path': self.photo_path,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
