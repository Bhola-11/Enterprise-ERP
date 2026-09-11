from django.db import models
from hr.models import Employee

class Driver(models.Model):
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='driver_profile')
    license_number = models.CharField(max_length=50, unique=True)
    license_expiry = models.DateField()
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.employee.full_name} (Lic: {self.license_number})"

class Vehicle(models.Model):
    STATUS_CHOICES = [
        ('ACTIVE', 'Active & On Route'),
        ('AVAILABLE', 'Available at Depot'),
        ('MAINTENANCE', 'Under Service / Repair'),
        ('RETIRED', 'Retired'),
    ]

    plate_number = models.CharField(max_length=30, unique=True)
    make = models.CharField(max_length=50) # Ford, Toyota, Mercedes, Volvo
    model = models.CharField(max_length=50) # Transit 350, Sprinter, Hilux
    year = models.PositiveSmallIntegerField(default=2024)
    vin = models.CharField(max_length=50, unique=True, blank=True, null=True)
    fuel_type = models.CharField(max_length=30, choices=[('DIESEL', 'Diesel'), ('PETROL', 'Gasoline/Petrol'), ('ELECTRIC', 'Electric'), ('HYBRID', 'Hybrid')], default='DIESEL')
    current_odometer_km = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AVAILABLE')
    assigned_driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_vehicles')
    insurance_expiry = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['plate_number']

    def __str__(self):
        return f"{self.plate_number} - {self.make} {self.model} ({self.get_status_display()})"

class FuelLog(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='fuel_logs')
    date = models.DateField()
    liters = models.DecimalField(max_digits=8, decimal_places=2)
    cost_per_liter = models.DecimalField(max_digits=6, decimal_places=2)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    odometer_km = models.PositiveIntegerField()
    station = models.CharField(max_length=100, default='Shell Fleet Station')

    def save(self, *args, **kwargs):
        self.total_cost = self.liters * self.cost_per_liter
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.vehicle.plate_number} - {self.liters}L on {self.date} (${self.total_cost:,.2f})"

class TripRecord(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='trips')
    driver = models.ForeignKey(Driver, on_delete=models.PROTECT, related_name='trips')
    date = models.DateField()
    start_location = models.CharField(max_length=150)
    end_location = models.CharField(max_length=150)
    distance_km = models.DecimalField(max_digits=8, decimal_places=2)
    purpose = models.CharField(max_length=255) # Client delivery, warehouse inter-transfer

    def __str__(self):
        return f"Trip: {self.start_location} -> {self.end_location} ({self.distance_km} km)"
