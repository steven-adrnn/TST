export default function handler(req, res) {
    const users = [
        { id: 1, name: 'John Doe' },
        { id: 2, name: 'Jane Smith' },
    ];

    res.status(200).json(users);
}