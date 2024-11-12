export default function handler(req, res) {
    const tools = [
        { id: 1, name: 'Cangkul' },
        { id: 2, name: 'Pupuk' },
        { id: 3, name: 'Sprayer' },
    ];

    res.status(200).json(tools);
}